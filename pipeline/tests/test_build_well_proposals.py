"""End-to-end tests through the pipeline's top-level function (Seam 1)."""

from __future__ import annotations

import copy
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from wildcat_pipeline import (
    WELL_PROPOSALS_SCHEMA,
    ContractError,
    LeakError,
    NoSummaryWriter,
    SummaryWriterError,
    build_well_proposals,
    load_snapshot,
    summary_review,
)

FIXTURE = Path(__file__).parent / "fixtures" / "snapshot"


BUILD_DATE = date(2026, 11, 19)


def build(writer: Any = None) -> dict[str, Any]:
    return build_well_proposals(
        load_snapshot(FIXTURE), writer or NoSummaryWriter(), build_date=BUILD_DATE
    )


def by_name(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["reveal"]["well_name"]: p for p in dataset["well_proposals"]}


def test_only_main_wildcat_wellbores_with_a_known_result_are_prospects() -> None:
    names = set(by_name(build()))

    assert names == {"34/10-1", "2/4-3", "25/7-1", "15/9-19", "7120/12-1", "30/6-5"}
    # appraisal 34/10-2, sidetrack 15/9-19 S and unknown-result 6/3-1 are out;
    # the frontier well 7120/12-1 is kept.


def test_outcome_is_discovery_or_dry_and_shows_count_as_dry() -> None:
    outcomes = {name: p["reveal"]["outcome"] for name, p in by_name(build()).items()}

    assert outcomes == {
        "34/10-1": "Discovery",  # OIL
        "2/4-3": "Dry",  # DRY
        "25/7-1": "Dry",  # OIL SHOWS
        "15/9-19": "Discovery",  # GAS/CONDENSATE
        "7120/12-1": "Discovery",  # GAS
        "30/6-5": "Discovery",  # OIL/GAS/CONDENSATE
    }


def test_dossier_holds_position_block_water_depth_target_and_decade() -> None:
    dossier = by_name(build())["34/10-1"]["dossier"]

    assert dossier == {
        "summary": "",
        "operator": "Operator A",
        "map_position": {"lat": 61.2051, "lon": 2.1953},
        "block": "34/10",
        "water_depth_m": 135.0,
        "target_formation": "STATFJORD GP",
        "target_age": "EARLY JURASSIC",
        "decade": "1970s",
        "geologist_view": {
            "wlbMainArea": "NORTH SEA",
            "wlbNsDecDeg": 61.2051,
            "wlbEwDecDeg": 2.1953,
            "wlbWaterDepth": 135.0,
            "wlbFormationAtTd": "STATFJORD GP",
            "wlbAgeAtTd": "EARLY JURASSIC",
        },
    }


def test_reveal_holds_name_operator_year_outcome_discovery_and_hydrocarbon_levels() -> None:
    well_proposals = by_name(build())

    assert well_proposals["34/10-1"]["reveal"] == {
        "well_name": "34/10-1",
        "operator": "Nordhav Petroleum AS",
        "year": 1978,
        "outcome": "Discovery",
        "discovery_name": "TROLLHAUGEN",
        "field_name": "TROLLHAUGEN",
        "hydrocarbon_levels": [
            {"formation": "BRENT GP", "age": "MIDDLE JURASSIC"},
            {"formation": "STATFJORD GP", "age": "EARLY JURASSIC"},
        ],
    }
    assert well_proposals["2/4-3"]["reveal"] == {
        "well_name": "2/4-3",
        "operator": "Westshore Oil Norge",
        "year": 1971,
        "outcome": "Dry",
        "discovery_name": None,
        "field_name": None,
        "hydrocarbon_levels": [],
    }


# Everything in the fixture that must only ever appear in a Reveal: well and
# wellbore names, discovery and field names, real operators, and every year,
# including dates after the spud date (completion, discovery year, production).
REVEAL_ONLY = [
    "34/10-1", "2/4-3", "25/7-1", "15/9-19", "7120/12-1", "30/6-5",
    "TROLLHAUGEN", "ISBJELLET",
    "Nordhav", "Westshore", "Fjordgas", "Kystlys", "Polarsokkel",
    "1971", "1978", "1979", "1981", "1982", "1985", "1986", "1987", "1993", "1999", "2011",
]  # fmt: skip


@pytest.mark.parametrize("secret", REVEAL_ONLY)
def test_names_operators_and_years_appear_only_in_the_reveal(secret: str) -> None:
    for well_proposal in build()["well_proposals"]:
        outside_reveal = {k: v for k, v in well_proposal.items() if k != "reveal"}
        assert secret.lower() not in repr(outside_reveal).lower()


class LeakingSummaryWriter:
    """Fake summary writer that puts `text` in the summary of every Well Proposal."""

    def __init__(self, text: str) -> None:
        self.text = text

    def write(self, facts: dict[str, Any]) -> str:
        return f"A well_proposal in block {facts['block']}. {self.text}"


@pytest.mark.parametrize(
    "leak",
    [
        "This is well 34/10-1.",  # a well name
        "The well 15/9-19 was a success.",  # a well name holding its discovery's name
        "It found the TROLLHAUGEN discovery.",  # a discovery and field name
        "Drilled by Nordhav Petroleum AS.",  # a real operator
        "Spudded in 1978.",  # an exact year
        "Completed 04.12.1978.",  # a date on or after the spud date
    ],
)
def test_build_fails_when_a_summary_leaks(leak: str) -> None:
    with pytest.raises(LeakError):
        build(LeakingSummaryWriter(leak))


class MentioningSummaryWriter:
    """Fake summary writer that mentions `text` only where `facts[key] == value`."""

    def __init__(self, key: str, value: str, text: str) -> None:
        self.key, self.value, self.text = key, value, text

    def write(self, facts: dict[str, Any]) -> str:
        return self.text if facts[self.key] == self.value else ""


def test_build_fails_when_a_dossier_names_a_discovery_made_after_the_spud_date() -> None:
    # ISBJELLET was found in 1981, after both 1970s wells were spudded.
    with pytest.raises(LeakError):
        build(MentioningSummaryWriter("decade", "1970s", "Close to ISBJELLET."))


def test_a_dossier_may_name_a_discovery_made_before_the_spud_date() -> None:
    # TROLLHAUGEN was found in 1979, before every 1980s well was spudded.
    dataset = build(MentioningSummaryWriter("decade", "1980s", "Close to TROLLHAUGEN."))

    assert by_name(dataset)["25/7-1"]["dossier"]["summary"] == "Close to TROLLHAUGEN."


def test_success_rate_across_eligible_wells_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", logger="wildcat_pipeline"):
        build()

    assert "Success rate: 4 of 6 eligible wildcat wells are Discoveries (66.7%)" in caplog.text


def test_dataset_carries_version_build_date_source_and_economics() -> None:
    dataset = build()

    assert re.fullmatch(r"2026-11-19\.[0-9a-f]{8}", dataset["dataset_version"])
    assert dataset["build_date"] == "2026-11-19"
    assert dataset["source"] == {
        "name": "Sodir FactPages",
        "url": "https://factpages.sodir.no",
        "licence": "NLOD",
        "licence_url": "https://data.norge.no/nlod/en/2.0",
        "attribution": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Sodir.",
    }
    assert dataset["well_cost"] == 100
    assert dataset["discovery_payout"] == 300  # three times the Well Cost
    assert dataset["hint_prices"] == {}
    assert all(p["hints"] == {} for p in dataset["well_proposals"])


def test_dataset_matches_the_published_contract() -> None:
    dataset = build()

    jsonschema.validate(json.loads(json.dumps(dataset)), WELL_PROPOSALS_SCHEMA)


def test_well_proposal_ids_are_unique_and_stable_across_builds() -> None:
    first = {p["reveal"]["well_name"]: p["id"] for p in build()["well_proposals"]}
    second = {p["reveal"]["well_name"]: p["id"] for p in build()["well_proposals"]}

    assert first == second
    assert len(set(first.values())) == len(first)


def test_dataset_version_changes_when_content_changes() -> None:
    plain = build()["dataset_version"]

    assert build()["dataset_version"] == plain
    assert build(LeakingSummaryWriter("A fine structure."))["dataset_version"] != plain


class BrokenSummaryWriter:
    """Fake summary writer that breaks the contract by returning a non-string."""

    def write(self, facts: dict[str, Any]) -> Any:
        return 42


def test_build_fails_when_the_output_breaks_the_contract() -> None:
    with pytest.raises(ContractError):
        build(BrokenSummaryWriter())


def test_a_formation_sharing_its_name_with_a_later_field_is_not_a_leak() -> None:
    # 2/4-3 (1971) targets the TOR FM; the TOR field was only found in 1990.
    dataset = build(MentioningSummaryWriter("decade", "1970s", "The target is the Tor Formation chalk."))

    assert by_name(dataset)["2/4-3"]["dossier"]["target_formation"] == "TOR FM"


def test_a_discovery_is_dated_by_when_its_discovery_well_was_spudded() -> None:
    # ISBJELLET (found 1981 by 7120/12-1, spudded June 1981) was known when
    # 15/9-19 was spudded in November 1981, the same year.
    dataset = build(MentioningSummaryWriter("block", "15/9", "Like ISBJELLET."))

    assert by_name(dataset)["15/9-19"]["dossier"]["summary"] == "Like ISBJELLET."


def test_a_discovery_made_by_a_later_well_in_the_same_year_is_a_leak() -> None:
    # 15/9-19 (spudded November 1981) found its discovery after 7120/12-1 was
    # spudded in June 1981.
    with pytest.raises(LeakError):
        build(MentioningSummaryWriter("block", "7120/12", "Like 15/9-19."))


def test_a_discovery_dated_only_by_year_may_be_named_from_the_same_year() -> None:
    # HAVBRIS's discovery well is not in the snapshot; it was found in 1985,
    # the year 25/7-1 was spudded.
    dataset = build(MentioningSummaryWriter("block", "25/7", "Like HAVBRIS."))

    assert by_name(dataset)["25/7-1"]["dossier"]["summary"] == "Like HAVBRIS."


def test_a_discovery_dated_only_by_year_is_a_leak_before_that_year() -> None:
    # HAVBRIS was found in 1985, after 15/9-19 was spudded in 1981.
    with pytest.raises(LeakError):
        build(MentioningSummaryWriter("block", "15/9", "Like HAVBRIS."))


# The Dossier fields a summary writer may see: all known before the spud date.
PRE_SPUD_FIELDS = {
    "operator", "map_position", "block", "water_depth_m",
    "target_formation", "target_age", "decade", "geologist_view",
}  # fmt: skip


class RecordingSummaryWriter:
    """Fake summary writer that records the facts it is given."""

    def __init__(self) -> None:
        self.facts: list[dict[str, Any]] = []

    def write(self, facts: dict[str, Any]) -> str:
        self.facts.append(copy.deepcopy(facts))
        return "A tilted fault block."


def test_the_summary_writer_gets_only_pre_spud_fields() -> None:
    writer = RecordingSummaryWriter()
    dataset = build(writer)

    assert len(writer.facts) == len(dataset["well_proposals"])
    for facts, well_proposal in zip(writer.facts, dataset["well_proposals"], strict=True):
        assert set(facts) == PRE_SPUD_FIELDS
        assert facts == {k: v for k, v in well_proposal["dossier"].items() if k != "summary"}
    for secret in REVEAL_ONLY:
        assert secret.lower() not in repr(writer.facts).lower()


class LeaksFirstSummaryWriter:
    """Fake summary writer that leaks the operator `leaks` times per well, then writes a clean summary."""

    def __init__(self, leaks: int) -> None:
        self.leaks = leaks
        self.calls: Counter[str] = Counter()

    def write(self, facts: dict[str, Any]) -> str:
        self.calls[facts["block"]] += 1
        return "Drilled by Nordhav Petroleum AS." if self.calls[facts["block"]] <= self.leaks else "A tilted fault block."


def test_a_leaking_summary_is_retried_until_it_passes_the_leak_guard() -> None:
    writer = LeaksFirstSummaryWriter(leaks=2)
    dataset = build(writer)

    assert {p["dossier"]["summary"] for p in dataset["well_proposals"]} == {"A tilted fault block."}
    assert set(writer.calls.values()) == {3}


def test_build_fails_when_a_summary_still_leaks_after_every_retry() -> None:
    writer = LeaksFirstSummaryWriter(leaks=3)

    with pytest.raises(LeakError, match=r"(?s)summary still leaks after 3 attempts.*'Nordhav Petroleum AS'"):
        build(writer)
    assert set(writer.calls.values()) == {3}


class FailingSummaryWriter:
    """Fake summary writer that fails `failures` times per well, then writes a summary."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls: Counter[str] = Counter()

    def write(self, facts: dict[str, Any]) -> str:
        self.calls[facts["block"]] += 1
        if self.calls[facts["block"]] <= self.failures:
            raise SummaryWriterError("service unavailable")
        return "A tilted fault block."


def test_a_failed_summary_is_retried() -> None:
    dataset = build(FailingSummaryWriter(failures=2))

    assert {p["dossier"]["summary"] for p in dataset["well_proposals"]} == {"A tilted fault block."}


def test_a_summary_that_cannot_be_written_is_flagged_and_left_empty(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="wildcat_pipeline"):
        dataset = build(FailingSummaryWriter(failures=3))

    assert {p["dossier"]["summary"] for p in dataset["well_proposals"]} == {""}
    flagged = [r.getMessage() for r in caplog.records if "Flagged" in r.getMessage()]
    assert len(flagged) == 6
    assert all("service unavailable" in message for message in flagged)


class SometimesFailingSummaryWriter:
    """Fake summary writer that always fails for 1970s wells."""

    def write(self, facts: dict[str, Any]) -> str:
        if facts["decade"] == "1970s":
            raise SummaryWriterError("service unavailable")
        return f"A structure in block {facts['block']}."


def test_summary_review_shows_a_sample_beside_its_reveal_and_every_flagged_well() -> None:
    dataset = build(SometimesFailingSummaryWriter())

    review = summary_review(dataset, size=2)

    assert review == summary_review(dataset, size=2)  # the same sample every time
    sample, flagged = review.split("## Flagged")
    assert "2 of 4 summaries" in sample
    sampled = re.findall(r"^### (\S+) ", sample, re.MULTILINE)
    assert len(sampled) == 2
    for name in sampled:
        well_proposal = by_name(dataset)[name]
        assert f"> {well_proposal['dossier']['summary']}" in sample
        assert well_proposal["reveal"]["outcome"] in sample
    assert set(re.findall(r"^- (\S+) ", flagged, re.MULTILINE)) == {"34/10-1", "2/4-3"}


def test_summary_review_samples_every_summary_when_there_are_few() -> None:
    dataset = build(SometimesFailingSummaryWriter())

    review = summary_review(dataset, size=20)

    assert "4 of 4 summaries" in review
