"""Reading FactPages cells, which the loader keeps as text ("" when empty)."""

from __future__ import annotations


def text(value: object) -> str | None:
    """The cell's text, or None if it is empty."""
    stripped = str(value).strip()
    return stripped or None


def number(value: object) -> float | None:
    """The cell as a number, or None if it is empty."""
    stripped = str(value).strip()
    return float(stripped) if stripped else None
