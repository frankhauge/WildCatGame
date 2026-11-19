"""Dossier builder (ADR 0001): what the Player sees before deciding.

Built only from data that existed before the well's spud date. The well's
name, the real operator and the exact year are left out; they go in the
Reveal instead.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .summary import SummaryWriter

HIDDEN_OPERATOR = "Operator A"

# Raw Sodir fields shown in the Geologist View. Every one must be known
# before the spud date.
_GEOLOGIST_VIEW_TEXT = ["wlbMainArea"]
_GEOLOGIST_VIEW_NUMBERS = ["wlbNsDecDeg", "wlbEwDecDeg", "wlbWaterDepth"]
_GEOLOGIST_VIEW_TARGET = ["wlbFormationAtTd", "wlbAgeAtTd"]


def build_dossier(
    row: pd.Series, spud_date: pd.Timestamp, summary_writer: SummaryWriter
) -> dict[str, Any]:
    """Build the Dossier for one eligible wellbore."""
    facts: dict[str, Any] = {
        "operator": HIDDEN_OPERATOR,
        "map_position": {"lat": _number(row["wlbNsDecDeg"]), "lon": _number(row["wlbEwDecDeg"])},
        "block": _block_of(str(row["wlbWell"])),
        "water_depth_m": _number(row["wlbWaterDepth"]),
        "target": {
            "formation": _text(row["wlbFormationAtTd"]),
            "age": _text(row["wlbAgeAtTd"]),
        },
        "decade": f"{spud_date.year // 10 * 10}s",
        "geologist_view": {
            **{field: _text(row[field]) for field in _GEOLOGIST_VIEW_TEXT},
            **{field: _number(row[field]) for field in _GEOLOGIST_VIEW_NUMBERS},
            **{field: _text(row[field]) for field in _GEOLOGIST_VIEW_TARGET},
        },
    }
    return {"summary": summary_writer.write(facts), **facts}


def _block_of(well_name: str) -> str:
    # Sodir well names are "<quadrant>/<block>-<number>", e.g. 34/10-1.
    return well_name.strip().split("-", 1)[0]


def _text(value: object) -> str | None:
    text = str(value).strip()
    return text or None


def _number(value: object) -> float | None:
    text = str(value).strip()
    return float(text) if text else None
