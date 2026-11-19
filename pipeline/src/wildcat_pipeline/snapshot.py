"""FactPages loader: reads a downloaded FactPages snapshot from files.

Downloading is deliberately not part of this module, so tests can supply a
hand-made fixture snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

WELLBORES_FILE = "wellbore_exploration_all.csv"
DISCOVERIES_FILE = "discovery.csv"


@dataclass(frozen=True)
class Snapshot:
    """The FactPages tables the pipeline reads, as loaded from one download."""

    wellbores: pd.DataFrame
    discoveries: pd.DataFrame


def load_snapshot(directory: Path | str) -> Snapshot:
    """Read a FactPages snapshot from a directory of CSV exports."""
    directory = Path(directory)
    return Snapshot(
        wellbores=_read_csv(directory / WELLBORES_FILE),
        discoveries=_read_csv(directory / DISCOVERIES_FILE),
    )


def spud_dates(wellbores: pd.DataFrame) -> pd.Series:
    """Each wellbore's spud date (Sodir's entry date), NaT where unknown.

    The spud date is the information boundary of ADR 0001.
    """
    return pd.to_datetime(wellbores["wlbEntryDate"].map(_parse_date))


def _parse_date(text: str) -> pd.Timestamp | None:
    # FactPages exports have used both ISO dates and Norwegian dd.mm.yyyy.
    text = text.strip()
    fmt = "%d.%m.%Y" if "." in text else "%Y-%m-%d"
    parsed = pd.to_datetime(text, format=fmt, errors="coerce")
    return None if pd.isna(parsed) else parsed


def _read_csv(path: Path) -> pd.DataFrame:
    # Read everything as text: Sodir codes such as licence "050" must keep
    # their leading zeros, and empty cells become "".
    return pd.read_csv(path, dtype=str, keep_default_na=False)
