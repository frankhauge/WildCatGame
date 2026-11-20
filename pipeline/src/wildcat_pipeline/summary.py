"""Summary writer: the injected interface that writes a Dossier's summary.

A summary is checked by the leak guard as soon as it is written (ADR 0001).
A summary that leaks, or that the writer fails to write, is asked for again,
up to MAX_ATTEMPTS times in all. A well whose summary still leaks fails the
build; a well whose summary could not be written is flagged and gets no
summary.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

log = logging.getLogger(__package__)

MAX_ATTEMPTS = 3


class SummaryWriter(Protocol):
    """Writes a plain-language summary from a Well Proposal's pre-spud facts only."""

    def write(self, facts: dict[str, Any]) -> str: ...


class SummaryWriterError(Exception):
    """A summary writer could not write a summary this time; it may succeed if asked again."""


class NoSummaryWriter:
    """A summary writer that writes nothing, for builds without summaries."""

    def write(self, facts: dict[str, Any]) -> str:
        return ""


def write_summary(
    writer: SummaryWriter,
    facts: dict[str, Any],
    breaches: Callable[[str], list[str]],
    well_proposal_id: str,
) -> tuple[str, list[str]]:
    """Write one well's summary, retrying leaks and failures.

    Returns the summary, and the breaches of the last attempt if every attempt
    failed and at least one leaked: an unresolved leak, which must fail the
    build. Otherwise the breaches are empty.
    """
    leaks: list[str] = []
    error: SummaryWriterError | None = None
    for _ in range(MAX_ATTEMPTS):
        try:
            summary = writer.write(facts)
        except SummaryWriterError as failure:
            error = failure
            continue
        if not isinstance(summary, str):
            # Not a summary at all: there is no text to guard, and the
            # contract check fails the build on it.
            return summary, []
        found = breaches(summary)
        if not found:
            return summary, []
        leaks = found
        log.info("Summary for %s leaks, asking again: %s", well_proposal_id, "; ".join(found))
    if leaks:
        return "", leaks
    log.warning(
        "Flagged %s: no summary after %d attempts: %s", well_proposal_id, MAX_ATTEMPTS, error
    )
    return "", []
