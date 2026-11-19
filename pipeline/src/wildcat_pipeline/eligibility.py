"""Eligibility filter: which FactPages wellbores can become Prospects."""

from __future__ import annotations

import logging

import pandas as pd

from .outcome import outcome_of
from .snapshot import spud_dates

log = logging.getLogger(__package__)

# Content values that honestly mean "no result", so are not worth a warning.
_NO_RESULT = {"", "NOT APPLICABLE", "NOT AVAILABLE"}


def eligible_wellbores(wellbores: pd.DataFrame) -> pd.DataFrame:
    """Keep wildcat main wellbores whose result and spud date are known.

    Frontier wells are kept: nothing here looks at neighbouring wells. A well
    without a spud date is left out, because its information boundary is
    unknown.
    """
    is_wildcat = wellbores["wlbPurpose"].str.strip().str.upper() == "WILDCAT"
    is_main = wellbores.apply(_is_main_wellbore, axis=1)
    has_result = wellbores["wlbContent"].map(lambda c: outcome_of(c) is not None)
    has_spud_date = spud_dates(wellbores).notna()

    candidates = wellbores[is_wildcat & is_main]
    unrecognised = set(candidates.loc[~has_result, "wlbContent"].str.strip().str.upper()) - _NO_RESULT
    if unrecognised:
        log.warning("Left out wildcat wells with unrecognised content values: %s", sorted(unrecognised))
    return wellbores[is_wildcat & is_main & has_result & has_spud_date]


def _is_main_wellbore(wellbore: pd.Series) -> bool:
    # A main wellbore is named after its well. When a well has been
    # sidetracked, Sodir gives the original wellbore the suffix "S"; the
    # sidetracks get other suffixes (A, B, T2, R for re-entries, ...).
    name = str(wellbore["wlbWellboreName"]).strip()
    well = str(wellbore["wlbWell"]).strip()
    return name in (well, f"{well} S")
