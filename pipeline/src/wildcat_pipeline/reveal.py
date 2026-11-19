"""Reveal section: what is shown only after the Player has decided."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .cells import text
from .outcome import outcome_of


def build_reveal(wellbore: pd.Series, spud_date: pd.Timestamp) -> dict[str, Any]:
    """The real well, its operator, year, Outcome, discovery or field, and the
    levels where hydrocarbons were found."""
    return {
        "well_name": text(wellbore["wlbWellboreName"]),
        "operator": text(wellbore["wlbDrillingOperator"]),
        "year": spud_date.year,
        "outcome": outcome_of(str(wellbore["wlbContent"])),
        "discovery_name": text(wellbore["wlbDiscovery"]),
        "field_name": text(wellbore["wlbField"]),
        "hydrocarbon_levels": _hydrocarbon_levels(wellbore),
    }


def _hydrocarbon_levels(wellbore: pd.Series) -> list[dict[str, str | None]]:
    # FactPages records up to three levels with hydrocarbons per wellbore.
    # They are known only after drilling, so they belong in the Reveal alone.
    levels = []
    for i in (1, 2, 3):
        formation = text(wellbore.get(f"wlbFormationWithHc{i}", ""))
        age = text(wellbore.get(f"wlbAgeWithHc{i}", ""))
        if formation or age:
            levels.append({"formation": formation, "age": age})
    return levels
