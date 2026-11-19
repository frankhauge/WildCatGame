"""Leak validator (ADR 0001): runs last and fails the build on any breach.

Outside a Prospect's Reveal, nothing may name:

- the well itself: its wellbore or well name, discovery or field name;
- any operator (the Dossier says "Operator A");
- an exact year or date;
- anything dated on or after the well's spud date: later wells, and
  discoveries or fields made in or after the spud year.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import pandas as pd

from .dossier import HIDDEN_OPERATOR
from .snapshot import Snapshot, spud_date_of

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


class LeakError(Exception):
    """The Prospects dataset breaks the information boundary."""


def validate_no_leaks(dataset: dict[str, Any], snapshot: Snapshot) -> None:
    """Raise LeakError listing every breach found outside the Reveals."""
    wellbores = snapshot.wellbores.assign(
        _spud=snapshot.wellbores.apply(spud_date_of, axis=1)
    ).set_index("wlbWellboreName", drop=False)
    operators = _names(wellbores["wlbDrillingOperator"]) - {HIDDEN_OPERATOR}

    breaches: list[str] = []
    for prospect in dataset["prospects"]:
        well = wellbores.loc[prospect["reveal"]["well_name"]]
        forbidden = operators | _own_names(well) | _names_dated_from(well["_spud"], wellbores, snapshot)
        for path, text in _strings({k: v for k, v in prospect.items() if k != "reveal"}):
            where = f"{prospect['id']} {path}"
            breaches += [f"{where}: names {term!r}" for term in sorted(forbidden) if term.lower() in text.lower()]
            breaches += [f"{where}: exact year {year!r}" for year in _YEAR.findall(text)]

    if breaches:
        raise LeakError("Information boundary breached:\n" + "\n".join(breaches))


def _own_names(well: pd.Series) -> set[str]:
    return _names(well[["wlbWellboreName", "wlbWell", "wlbDiscovery", "wlbField"]])


def _names_dated_from(spud: pd.Timestamp, wellbores: pd.DataFrame, snapshot: Snapshot) -> set[str]:
    later_wells = wellbores[wellbores["_spud"] >= spud]
    discoveries = snapshot.discoveries
    later_discoveries = discoveries[discoveries["dscDiscoveryYear"].astype(int) >= spud.year]
    return (
        _names(later_wells["wlbWellboreName"])
        | _names(later_wells["wlbWell"])
        | _names(later_wells["wlbDiscovery"])
        | _names(later_wells["wlbField"])
        | _names(later_discoveries["dscName"])
        | _names(later_discoveries["fldName"])
    )


def _names(values: pd.Series) -> set[str]:
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
