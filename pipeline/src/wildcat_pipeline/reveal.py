"""Reveal section: what is shown only after the Player has decided."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .cells import text
from .outcome import outcome_of


def build_reveal(wellbore: pd.Series, spud_date: pd.Timestamp) -> dict[str, Any]:
    """The real well, its operator, year, Outcome and discovery or field."""
    return {
        "well_name": text(wellbore["wlbWellboreName"]),
        "operator": text(wellbore["wlbDrillingOperator"]),
        "year": spud_date.year,
        "outcome": outcome_of(str(wellbore["wlbContent"])),
        "discovery_name": text(wellbore["wlbDiscovery"]),
        "field_name": text(wellbore["wlbField"]),
    }
