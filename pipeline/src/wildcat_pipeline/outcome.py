"""Outcome mapper: Sodir's wellbore content value to Discovery or Dry."""

from __future__ import annotations

from typing import Literal

Outcome = Literal["Discovery", "Dry"]

_DISCOVERY_CONTENTS = {"OIL", "GAS", "OIL/GAS", "GAS/CONDENSATE", "OIL/GAS/CONDENSATE"}


def outcome_of(content: str) -> Outcome | None:
    """Map a wlbContent value to an Outcome, or None if the result is unknown.

    A well with only shows counts as Dry.
    """
    value = content.strip().upper()
    if value in _DISCOVERY_CONTENTS:
        return "Discovery"
    if value == "DRY" or value.endswith("SHOWS"):
        return "Dry"
    return None
