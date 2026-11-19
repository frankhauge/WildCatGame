"""Dossier builder (ADR 0001): what the Player sees before deciding.

Built only from data that existed before the well's spud date. The well's
name, the real operator and the exact year are left out; they go in the
Reveal instead.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .cells import number, text
from .summary import SummaryWriter

HIDDEN_OPERATOR = "Operator A"

# Raw Sodir fields shown in the Geologist View. Every one must be known
# before the spud date.
_GEOLOGIST_VIEW_TEXT = ["wlbMainArea", "wlbFormationAtTd", "wlbAgeAtTd"]
_GEOLOGIST_VIEW_NUMBERS = ["wlbNsDecDeg", "wlbEwDecDeg", "wlbWaterDepth"]


def build_dossier(
    wellbore: pd.Series, spud_date: pd.Timestamp, summary_writer: SummaryWriter
) -> dict[str, Any]:
    """Build the Dossier for one eligible wellbore."""
    facts: dict[str, Any] = {
        "operator": HIDDEN_OPERATOR,
        "map_position": {
            "lat": number(wellbore["wlbNsDecDeg"]),
            "lon": number(wellbore["wlbEwDecDeg"]),
        },
        "block": _block_of(str(wellbore["wlbWell"])),
        "water_depth_m": number(wellbore["wlbWaterDepth"]),
        "target_formation": text(wellbore["wlbFormationAtTd"]),
        "target_age": text(wellbore["wlbAgeAtTd"]),
        "decade": f"{spud_date.year // 10 * 10}s",
        "geologist_view": {
            **{field: text(wellbore[field]) for field in _GEOLOGIST_VIEW_TEXT},
            **{field: number(wellbore[field]) for field in _GEOLOGIST_VIEW_NUMBERS},
        },
    }
    return {"summary": summary_writer.write(facts), **facts}


def _block_of(well_name: str) -> str:
    # Sodir well names are "<quadrant>/<block>-<number>", e.g. 34/10-1.
    return well_name.strip().split("-", 1)[0]
