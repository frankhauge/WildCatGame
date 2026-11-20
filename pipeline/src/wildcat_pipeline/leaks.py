"""Leak validator (ADR 0001): runs last and fails the build on any breach.

Outside a Well Proposal's Reveal (in its Dossier and Hints, and in the Hint
prices), nothing may name:

- the well itself: its wellbore or well name, discovery or field name;
- any operator (the Dossier says "Operator A");
- an exact year or date;
- anything dated on or after the well's spud date: later wells, and later
  discoveries with their fields.

A discovery is dated by the spud date of the wellbore that made it: it is
later if that wellbore was spudded on or after this well's spud date. When
the discovery wellbore is not in the snapshot, the discovery year dates it,
and a discovery in the spud year counts as earlier. Unknown dates count as
later. Names are matched as whole words, ignoring
geological units such as "Tor Formation" or "STATFJORD GP": many fields are
named after the formation they produce from, and a formation existed long
before the well.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from functools import cache
from typing import Any

import pandas as pd

from .dossier import HIDDEN_OPERATOR
from .snapshot import Snapshot, spud_dates

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_GEOLOGICAL_UNIT = re.compile(r"\b[\w-]+\s+(?:fm|formation|gp|group)\b", re.IGNORECASE)


class LeakError(Exception):
    """The Well Proposals dataset breaks the information boundary."""


def validate_no_leaks(dataset: dict[str, Any], snapshot: Snapshot) -> None:
    """Raise LeakError listing every breach found outside the Reveals."""
    wellbores = snapshot.wellbores.assign(spud=spud_dates(snapshot.wellbores))
    discoveries = _dated_discoveries(snapshot.discoveries, wellbores)
    operators = _names(wellbores["wlbDrillingOperator"]) - {HIDDEN_OPERATOR}
    hint_kinds = " ".join(dataset["hint_prices"])
    mentioned = _mention_finder(
        operators
        | _names(wellbores[["wlbWellboreName", "wlbWell", "wlbDiscovery", "wlbField"]].to_numpy().ravel())
        | _names(discoveries["dscName"])
        | _names(discoveries["fldName"])
    )

    breaches: list[str] = []
    for well_proposal in dataset["well_proposals"]:
        well = wellbores[wellbores["wlbWellboreName"] == well_proposal["reveal"]["well_name"]].iloc[0]
        forbidden = operators | _own_names(well) | _names_dated_from(well["spud"], wellbores, discoveries)
        outside_reveal = {k: v for k, v in well_proposal.items() if k != "reveal"}
        for path, text in [*_strings(outside_reveal), ("hint_prices", hint_kinds)]:
            where = f"{well_proposal['id']} {path}"
            breaches += [f"{where}: names {name!r}" for name in sorted(mentioned(text) & forbidden)]
            breaches += [f"{where}: exact year {year!r}" for year in _YEAR.findall(text)]

    if breaches:
        raise LeakError("Information boundary breached:\n" + "\n".join(breaches))


def _own_names(well: pd.Series) -> set[str]:
    return _names(well[["wlbWellboreName", "wlbWell", "wlbDiscovery", "wlbField"]])


def _names_dated_from(
    spud: pd.Timestamp, wellbores: pd.DataFrame, discoveries: pd.DataFrame
) -> set[str]:
    later_wells = wellbores[wellbores["spud"].isna() | (wellbores["spud"] >= spud)]
    by_well = discoveries["found_by_spud"] >= spud
    by_year = discoveries["found_by_spud"].isna() & (discoveries["year"] > spud.year)
    undated = discoveries["found_by_spud"].isna() & discoveries["year"].isna()
    later_discoveries = discoveries[by_well | by_year | undated]
    return (
        _names(later_wells["wlbWellboreName"])
        | _names(later_wells["wlbWell"])
        | _names(later_discoveries["dscName"])
        | _names(later_discoveries["fldName"])
    )


def _dated_discoveries(discoveries: pd.DataFrame, wellbores: pd.DataFrame) -> pd.DataFrame:
    """Discoveries with their year and the spud date of their discovery wellbore."""
    spud_by_name = wellbores.set_index("wlbWellboreName")["spud"]
    spud_by_name = spud_by_name[~spud_by_name.index.duplicated()]
    return discoveries.assign(
        year=pd.to_numeric(discoveries["dscDiscoveryYear"], errors="coerce"),
        found_by_spud=discoveries["wlbName"].str.strip().map(spud_by_name),
    )


def _mention_finder(names: set[str]) -> Callable[[str], frozenset[str]]:
    """A function giving the names, out of `names`, that a text mentions.

    A real snapshot has thousands of names and Dossiers repeat the same short
    texts, so each distinct text is checked once, and only names it contains
    as a substring get the slower whole-word check.
    """
    folded = [(name, name.casefold()) for name in names]

    @cache
    def mentioned(text: str) -> frozenset[str]:
        prose = _GEOLOGICAL_UNIT.sub(" ", text)
        folded_prose = prose.casefold()
        return frozenset(
            name for name, folded_name in folded if folded_name in folded_prose and _mentions(prose, name)
        )

    return mentioned


def _mentions(prose: str, name: str) -> bool:
    # Whole words only, so "2/4-3" is not found inside "12/4-31" and "TOR"
    # not inside "Operator".
    return re.search(rf"(?<![\w/-]){re.escape(name)}(?![\w/-])", prose, re.IGNORECASE) is not None


def _names(values: Iterable[object]) -> set[str]:
    return {str(v).strip() for v in values if str(v).strip()}


def _strings(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{path}[{index}]")
