"""Tests through the Claude summary writer, with a fake client instead of the Claude API."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from wildcat_pipeline import (
    ClaudeSummaryWriter,
    SummaryWriterError,
    build_well_proposals,
    load_snapshot,
)

FIXTURE = Path(__file__).parent / "fixtures" / "snapshot"

FACTS = {
    "operator": "Operator A",
    "map_position": {"lat": 61.2051, "lon": 2.1953},
    "block": "34/10",
    "water_depth_m": 135.0,
    "decade": "1970s",
    "geologist_view": {"wlbMainArea": "NORTH SEA"},
}


def text(value: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=value)


def response(*content: SimpleNamespace, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=list(content))


class FakeClient:
    """Stands in for anthropic.Anthropic: records requests and returns canned responses."""

    def __init__(self, *responses: SimpleNamespace) -> None:
        self.requests: list[dict[str, Any]] = []
        self.responses = list(responses)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **request: Any) -> SimpleNamespace:
        self.requests.append(request)
        return self.responses[min(len(self.requests), len(self.responses)) - 1]


def writer(client: FakeClient) -> ClaudeSummaryWriter:
    return ClaudeSummaryWriter(client=cast(Any, client))


def test_sends_only_the_facts_it_is_given() -> None:
    client = FakeClient(response(text("A summary.")))

    writer(client).write(FACTS)

    (request,) = client.requests
    assert request["messages"] == [{"role": "user", "content": json.dumps(FACTS, indent=2)}]
    # The instructions are the same for every well, so nothing else about the
    # well can reach the model.
    other = FakeClient(response(text("A summary.")))
    writer(other).write({**FACTS, "block": "2/4"})
    assert other.requests[0]["system"] == request["system"]


def test_returns_the_text_of_the_reply() -> None:
    client = FakeClient(
        response(SimpleNamespace(type="thinking", thinking=""), text("  A tilted fault block.  "))
    )

    assert writer(client).write(FACTS) == "A tilted fault block."


@pytest.mark.parametrize(
    "reply",
    [
        response(text("I can't help with that."), stop_reason="refusal"),
        response(text("A tilted fault"), stop_reason="max_tokens"),
        response(text("   ")),
    ],
)
def test_fails_when_the_reply_is_not_a_whole_summary(reply: SimpleNamespace) -> None:
    with pytest.raises(SummaryWriterError):
        writer(FakeClient(reply)).write(FACTS)


def test_writes_every_dossier_summary_in_a_build() -> None:
    client = FakeClient(response(text("A tilted fault block in the northern North Sea.")))

    dataset = build_well_proposals(load_snapshot(FIXTURE), writer(client), build_date=date(2026, 11, 20))

    assert {p["dossier"]["summary"] for p in dataset["well_proposals"]} == {
        "A tilted fault block in the northern North Sea."
    }
