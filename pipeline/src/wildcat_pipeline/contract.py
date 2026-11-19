"""The Well Proposals dataset contract, published as a JSON Schema."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

import jsonschema

WELL_PROPOSALS_SCHEMA: dict[str, Any] = json.loads(
    files(__package__).joinpath("well_proposals.schema.json").read_text(encoding="utf-8")
)


class ContractError(Exception):
    """The Well Proposals dataset does not match its contract."""


def validate_contract(dataset: dict[str, Any]) -> None:
    """Raise ContractError if the dataset does not match the published schema."""
    validator = jsonschema.Draft202012Validator(WELL_PROPOSALS_SCHEMA)
    errors = sorted(validator.iter_errors(dataset), key=lambda e: list(e.absolute_path))
    if errors:
        raise ContractError(
            "Well Proposals dataset breaks its contract:\n"
            + "\n".join(f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors)
        )
