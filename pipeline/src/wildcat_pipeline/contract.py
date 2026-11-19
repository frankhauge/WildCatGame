"""The Prospects dataset contract, published as a JSON Schema."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

import jsonschema

PROSPECTS_SCHEMA: dict[str, Any] = json.loads(
    files(__package__).joinpath("prospects.schema.json").read_text(encoding="utf-8")
)


class ContractError(Exception):
    """The Prospects dataset does not match its contract."""


def validate_contract(dataset: dict[str, Any]) -> None:
    """Raise ContractError if the dataset does not match the published schema."""
    validator = jsonschema.Draft202012Validator(PROSPECTS_SCHEMA)
    errors = sorted(validator.iter_errors(dataset), key=lambda e: list(e.absolute_path))
    if errors:
        raise ContractError(
            "Prospects dataset breaks its contract:\n"
            + "\n".join(f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors)
        )
