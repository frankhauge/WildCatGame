"""Summary writer: the injected interface that writes a Dossier's summary."""

from __future__ import annotations

from typing import Any, Protocol


class SummaryWriter(Protocol):
    """Writes a plain-language summary from a Well Proposal's pre-spud facts only."""

    def write(self, facts: dict[str, Any]) -> str: ...


class NoSummaryWriter:
    """A summary writer that writes nothing, until the LLM writer exists."""

    def write(self, facts: dict[str, Any]) -> str:
        return ""
