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


def _read_csv(path: Path) -> pd.DataFrame:
    # Read everything as text: Sodir codes such as licence "050" must keep
    # their leading zeros, and empty cells become "".
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def spud_date_of(wellbore: pd.Series) -> pd.Timestamp:
    """The date drilling started (Sodir's entry date), the information boundary."""
    return _parse_date(str(wellbore["wlbEntryDate"]))


def _parse_date(text: str) -> pd.Timestamp:
    # FactPages exports have used both ISO dates and Norwegian dd.mm.yyyy.
    text = text.strip()
    fmt = "%d.%m.%Y" if "." in text else "%Y-%m-%d"
    return pd.to_datetime(text, format=fmt)
