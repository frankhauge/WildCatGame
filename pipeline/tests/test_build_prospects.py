"""End-to-end tests through the pipeline's top-level function (Seam 1)."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from wildcat_pipeline import (
    PROSPECTS_SCHEMA,
    ContractError,
    LeakError,
    build_prospects,
    load_snapshot,
)

FIXTURE = Path(__file__).parent / "fixtures" / "snapshot"


class SilentSummaryWriter:
    """Fake summary writer that writes nothing."""

    def write(self, facts: dict[str, Any]) -> str:
        return ""


BUILD_DATE = date(2026, 11, 19)


def build(writer: Any = None) -> dict[str, Any]:
    return build_prospects(
        load_snapshot(FIXTURE), writer or SilentSummaryWriter(), build_date=BUILD_DATE
    )


def by_name(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["reveal"]["well_name"]: p for p in dataset["prospects"]}


def test_only_main_wildcat_wellbores_with_a_known_result_are_prospects() -> None:
    names = set(by_name(build()))

    assert names == {"34/10-1", "2/4-3", "25/7-1", "15/9-19 S", "7120/12-1"}
    # appraisal 34/10-2, sidetrack 15/9-19 A and unknown-result 6/3-1 are out;
    # the frontier well 7120/12-1 is kept.


def test_outcome_is_discovery_or_dry_and_shows_count_as_dry() -> None:
    outcomes = {name: p["reveal"]["outcome"] for name, p in by_name(build()).items()}

    assert outcomes == {
        "34/10-1": "Discovery",  # OIL
        "2/4-3": "Dry",  # DRY
        "25/7-1": "Dry",  # OIL SHOWS
        "15/9-19 S": "Discovery",  # GAS/CONDENSATE
        "7120/12-1": "Discovery",  # GAS
    }


def test_dossier_holds_position_block_water_depth_target_and_decade() -> None:
    dossier = by_name(build())["34/10-1"]["dossier"]

    assert dossier == {
        "summary": "",
        "operator": "Operator A",
        "map_position": {"lat": 61.2051, "lon": 2.1953},
        "block": "34/10",
        "water_depth_m": 135.0,
        "target": {"formation": "STATFJORD GP", "age": "EARLY JURASSIC"},
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


def test_reveal_holds_name_operator_year_outcome_and_discovery() -> None:
    prospects = by_name(build())

    assert prospects["34/10-1"]["reveal"] == {
        "well_name": "34/10-1",
        "operator": "Nordhav Petroleum AS",
        "year": 1978,
        "outcome": "Discovery",
        "discovery_name": "TROLLHAUGEN",
        "field_name": "TROLLHAUGEN",
    }
    assert prospects["2/4-3"]["reveal"] == {
        "well_name": "2/4-3",
        "operator": "Westshore Oil Norge",
        "year": 1971,
        "outcome": "Dry",
        "discovery_name": None,
        "field_name": None,
    }


# Everything in the fixture that must only ever appear in a Reveal: well and
# wellbore names, discovery and field names, real operators, and every year,
# including dates after the spud date (completion, discovery year, production).
REVEAL_ONLY = [
    "34/10-1", "2/4-3", "25/7-1", "15/9-19", "7120/12-1",
    "TROLLHAUGEN", "ISBJELLET",
    "Nordhav", "Westshore", "Fjordgas", "Kystlys", "Polarsokkel",
    "1971", "1978", "1979", "1981", "1982", "1985", "1987", "1993", "2011",
]  # fmt: skip


@pytest.mark.parametrize("secret", REVEAL_ONLY)
def test_names_operators_and_years_appear_only_in_the_reveal(secret: str) -> None:
    for prospect in build()["prospects"]:
        outside_reveal = {k: v for k, v in prospect.items() if k != "reveal"}
        assert secret.lower() not in repr(outside_reveal).lower()


class LeakingSummaryWriter:
    """Fake summary writer that puts `text` in the summary of every Prospect."""

    def __init__(self, text: str) -> None:
        self.text = text

    def write(self, facts: dict[str, Any]) -> str:
        return f"A prospect in block {facts['block']}. {self.text}"


@pytest.mark.parametrize(
    "leak",
    [
        "This is well 34/10-1.",  # a well name
        "The well 15/9-19 S was a success.",  # a well name holding its discovery's name
        "It found the TROLLHAUGEN discovery.",  # a discovery and field name
        "Drilled by Nordhav Petroleum AS.",  # a real operator
        "Spudded in 1978.",  # an exact year
        "Completed 04.12.1978.",  # a date on or after the spud date
    ],
)
def test_build_fails_when_a_summary_leaks(leak: str) -> None:
    with pytest.raises(LeakError):
        build(LeakingSummaryWriter(leak))


class DecadeSummaryWriter:
    """Fake summary writer that mentions `text` only for Prospects of `decade`."""

    def __init__(self, decade: str, text: str) -> None:
        self.decade, self.text = decade, text

    def write(self, facts: dict[str, Any]) -> str:
        return self.text if facts["decade"] == self.decade else ""


def test_build_fails_when_a_dossier_names_a_discovery_made_after_the_spud_date() -> None:
    # ISBJELLET was found in 1982, after both 1970s wells were spudded.
    with pytest.raises(LeakError):
        build(DecadeSummaryWriter("1970s", "Close to ISBJELLET."))


def test_a_dossier_may_name_a_discovery_made_before_the_spud_date() -> None:
    # TROLLHAUGEN was found in 1979, before every 1980s well was spudded.
    dataset = build(DecadeSummaryWriter("1980s", "Close to TROLLHAUGEN."))

    assert by_name(dataset)["25/7-1"]["dossier"]["summary"] == "Close to TROLLHAUGEN."


def test_success_rate_across_eligible_wells_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", logger="wildcat_pipeline"):
        build()

    assert "Success rate: 3 of 5 eligible wildcat wells are Discoveries (60.0%)" in caplog.text


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
    assert all(p["hints"] == {} for p in dataset["prospects"])


def test_dataset_matches_the_published_contract() -> None:
    dataset = build()

    jsonschema.validate(json.loads(json.dumps(dataset)), PROSPECTS_SCHEMA)


def test_prospect_ids_are_unique_and_stable_across_builds() -> None:
    first = {p["reveal"]["well_name"]: p["id"] for p in build()["prospects"]}
    second = {p["reveal"]["well_name"]: p["id"] for p in build()["prospects"]}

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
