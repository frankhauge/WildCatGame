# Wildcat pipeline

Turns a Sodir FactPages snapshot into the versioned Well Proposals dataset (`well_proposals.json`), the only interface between the pipeline and the app. Vocabulary: [CONTEXT.md](../CONTEXT.md). Information boundary: [ADR 0001](../docs/adr/0001-information-boundary-at-spud-date.md).

## Run

```bash
pip install -e '.[dev]'
```

```bash
python -m wildcat_pipeline path/to/snapshot well_proposals.json
```

The snapshot directory holds FactPages CSV exports: `wellbore_exploration_all.csv` and `discovery.csv`. Downloading them is a separate step. Every run logs the success rate across all eligible wells.

The build fails with `ContractError` if the output does not match [`well_proposals.schema.json`](src/wildcat_pipeline/well_proposals.schema.json), and with `LeakError` if anything outside a Well Proposal's Reveal names a well, discovery, field or operator, gives an exact year, or names anything dated on or after the spud date.

## Test

```bash
python -m pytest
```

```bash
mypy
```

Tests go only through the top-level function, `build_well_proposals`, using the hand-made fixture in `tests/fixtures/`.
