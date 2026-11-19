"""Eligibility filter: which FactPages wellbores can become Prospects."""

from __future__ import annotations

import pandas as pd

from .outcome import outcome_of


def eligible_wellbores(wellbores: pd.DataFrame) -> pd.DataFrame:
    """Keep wildcat main wellbores whose result is known.

    Frontier wells are kept: nothing here looks at neighbouring wells.
    """
    is_wildcat = wellbores["wlbPurpose"].str.strip().str.upper() == "WILDCAT"
    is_main = wellbores.apply(_is_main_wellbore, axis=1)
    has_result = wellbores["wlbContent"].map(lambda c: outcome_of(c) is not None)
    return wellbores[is_wildcat & is_main & has_result]


def _is_main_wellbore(row: pd.Series) -> bool:
    # A main wellbore is named after its well. When a well has been
    # sidetracked, Sodir gives the original wellbore the suffix "S"; the
    # sidetracks get other suffixes (A, B, T2, R for re-entries, ...).
    name = str(row["wlbWellboreName"]).strip()
    well = str(row["wlbWell"]).strip()
    return name in (well, f"{well} S")
