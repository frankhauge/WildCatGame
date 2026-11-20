"""The production summary writer: asks Claude for each Dossier's summary.

Claude gets only the facts it is given, which the build takes from the
Dossier, so only pre-spud fields (ADR 0001). The model may still know from
training what a well found, so every summary goes through the leak guard.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from .summary import SummaryWriterError

MODEL = "claude-opus-5-5"

# The same for every well, so nothing but the facts varies per request.
INSTRUCTIONS = """\
You write the plain-language summary of a proposed exploration well for a game \
about drilling decisions on the Norwegian Continental Shelf. Players include \
non-experts, so explain what the facts mean in everyday words.

Write two or three short sentences of plain prose, without headings or lists, \
from the facts you are given and nothing else:

- Never name a well, discovery, field, licence or company. The operator is \
"Operator A".
- Never give a year or date. Say only the decade.
- Never say or hint whether the well found oil or gas, and never give a chance \
of success. The Player decides that.
"""


class ClaudeSummaryWriter:
    """Writes each summary with one Claude request."""

    def __init__(self, client: anthropic.Anthropic | None = None, model: str = MODEL) -> None:
        self._client = client or anthropic.Anthropic()
        self._model = model

    def write(self, facts: dict[str, Any]) -> str:
        try:
            response = self._client.beta.messages.create(
                model=self._model,
                max_tokens=8000,
                system=INSTRUCTIONS,
                messages=[{"role": "user", "content": json.dumps(facts, indent=2)}],
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError) as error:
            # Still failing after the SDK's own retries. Other API errors (a
            # bad key, a bad request) would fail for every well, so they stop
            # the build instead.
            raise SummaryWriterError(f"Claude request failed: {error}") from error

        if response.stop_reason != "end_turn":
            raise SummaryWriterError(f"Claude stopped with {response.stop_reason!r}")
        summary = "".join(block.text for block in response.content if block.type == "text").strip()
        if not summary:
            raise SummaryWriterError("Claude wrote an empty summary")
        return summary
