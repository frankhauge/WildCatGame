"""The pipeline's top-level function: FactPages snapshot to Well Proposals dataset."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date
from typing import Any

import pandas as pd

from .contract import validate_contract
from .dossier import dossier_facts
from .eligibility import eligible_wellbores
from .leaks import LeakError, LeakGuard, validate_no_leaks
from .reveal import build_reveal
from .snapshot import Snapshot, spud_dates
from .summary import MAX_ATTEMPTS, NoSummaryWriter, SummaryWriter, write_summary

log = logging.getLogger(__package__)

WELL_COST = 100
DISCOVERY_PAYOUT = 3 * WELL_COST

SOURCE = {
    "name": "Sodir FactPages",
    "url": "https://factpages.sodir.no",
    "licence": "NLOD",
    "licence_url": "https://data.norge.no/nlod/en/2.0",
    "attribution": (
        "Contains data under the Norwegian licence for Open Government data (NLOD) "
        "distributed by Sodir."
    ),
}


def build_well_proposals(
    snapshot: Snapshot,
    summary_writer: SummaryWriter,
    *,
    build_date: date | None = None,
) -> dict[str, Any]:
    """Turn a FactPages snapshot into a versioned Well Proposals dataset.

    Raises ContractError if the output does not match the dataset contract,
    and LeakError if it breaks the information boundary (ADR 0001), including
    when a summary still leaks after every retry.
    """
    build_date = build_date or date.today()
    guard = LeakGuard(snapshot)
    well_proposals = []
    unresolved_leaks: list[str] = []
    wells = eligible_wellbores(snapshot.wellbores)
    for (_, wellbore), spud_date in zip(wells.iterrows(), spud_dates(wells), strict=True):
        wp_id = well_proposal_id(wellbore)
        reveal = build_reveal(wellbore, spud_date)
        facts = dossier_facts(wellbore, spud_date)
        summary, leaks = write_summary(
            summary_writer, facts, lambda text: guard.breaches(text, reveal["well_name"]), wp_id
        )
        unresolved_leaks += [
            f"{wp_id} summary still leaks after {MAX_ATTEMPTS} attempts: {leak}" for leak in leaks
        ]
        well_proposals.append(
            {"id": wp_id, "dossier": {"summary": summary, **facts}, "hints": {}, "reveal": reveal}
        )
    if unresolved_leaks:
        raise LeakError("Information boundary breached:\n" + "\n".join(unresolved_leaks))
    _log_success_rate(well_proposals)
    _log_summaries(well_proposals, summary_writer)

    hint_prices: dict[str, int] = {}
    dataset = {
        "dataset_version": _dataset_version(build_date, hint_prices, well_proposals),
        "build_date": build_date.isoformat(),
        "source": SOURCE,
        "well_cost": WELL_COST,
        "discovery_payout": DISCOVERY_PAYOUT,
        "hint_prices": hint_prices,
        "well_proposals": well_proposals,
    }
    validate_contract(dataset)
    validate_no_leaks(dataset, guard)  # always last
    return dataset


def well_proposal_id(wellbore: pd.Series) -> str:
    """A stable ID that does not show the well's name.

    Derived from Sodir's wellbore NPDID, which never changes. Hex only, so it
    cannot contain a year-like word.
    """
    digest = hashlib.sha256(f"wildcat:{wellbore['wlbNpdidWellbore']}".encode()).hexdigest()
    return f"WP{digest[:12]}"


def _dataset_version(
    build_date: date, hint_prices: dict[str, int], well_proposals: list[dict[str, Any]]
) -> str:
    # The build date plus a hash of the content, so the same content always
    # gets the same version and Decision Records can name what was shown.
    content = json.dumps(
        {"well_cost": WELL_COST, "hint_prices": hint_prices, "well_proposals": well_proposals},
        sort_keys=True,
        default=str,
    )
    return f"{build_date.isoformat()}.{hashlib.sha256(content.encode()).hexdigest()[:8]}"


def _log_success_rate(well_proposals: list[dict[str, Any]]) -> None:
    # Logged on every run so the game balance (budget, payout) can be checked
    # against the real success rate.
    discoveries = sum(p["reveal"]["outcome"] == "Discovery" for p in well_proposals)
    rate = discoveries / len(well_proposals) if well_proposals else 0.0
    log.info(
        "Success rate: %d of %d eligible wildcat wells are Discoveries (%.1f%%)",
        discoveries,
        len(well_proposals),
        100 * rate,
    )


def _log_summaries(well_proposals: list[dict[str, Any]], summary_writer: SummaryWriter) -> None:
    if isinstance(summary_writer, NoSummaryWriter):
        return
    missing = sum(p["dossier"]["summary"] == "" for p in well_proposals)
    log.info("Summaries: %d written, %d flagged", len(well_proposals) - missing, missing)
