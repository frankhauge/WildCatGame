"""Reveal section: what is shown only after the Player has decided."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .outcome import outcome_of


def build_reveal(row: pd.Series, spud_date: pd.Timestamp) -> dict[str, Any]:
    """The real well, its operator, year, Outcome and discovery or field."""
    return {
        "well_name": _text(row["wlbWellboreName"]),
        "operator": _text(row["wlbDrillingOperator"]),
        "year": spud_date.year,
        "outcome": outcome_of(str(row["wlbContent"])),
        "discovery_name": _text(row["wlbDiscovery"]),
        "field_name": _text(row["wlbField"]),
    }


def _text(value: object) -> str | None:
    text = str(value).strip()
    return text or None
