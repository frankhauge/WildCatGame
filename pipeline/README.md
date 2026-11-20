# Wildcat pipeline

Turns a Sodir FactPages snapshot into the versioned Well Proposals dataset (`well_proposals.json`), the only interface between the pipeline and the app. Vocabulary: [CONTEXT.md](../CONTEXT.md). Information boundary: [ADR 0001](../docs/adr/0001-information-boundary-at-spud-date.md).

## Run

```bash
pip install -e '.[dev]'
```

```bash
python -m wildcat_pipeline build path/to/snapshot well_proposals.json
```

A snapshot is a directory of FactPages CSV exports. The build reads `wellbore_exploration_all.csv` and `discovery.csv`. Downloading is a separate step (below), so tests use the fixture snapshot and never the network. Every run logs the success rate across all eligible wells.

The build fails with `ContractError` if the output does not match [`well_proposals.schema.json`](src/wildcat_pipeline/well_proposals.schema.json), and with `LeakError` if anything outside a Well Proposal's Reveal names a well, discovery, field or operator, gives an exact year, or names anything dated on or after the spud date.

## Refresh the dataset

Run these by hand from `pipeline/` whenever new wells should come into the game. No code changes are needed.

1. Download a fresh snapshot into a new directory named after today's date:

   ```bash
   python -m wildcat_pipeline download snapshots/$(date +%F)
   ```

   This saves the tables the game uses: wellbores, discoveries, fields, licences, seismic surveys (`survey.csv`) and block outlines (`blkArea.csv`, WKT polygons). `snapshot.json` records when and from which URL each file came. It takes under a minute. A snapshot is never overwritten, and a failed download leaves nothing behind. `snapshots/` is not committed.

2. Build the dataset the app ships:

   ```bash
   python -m wildcat_pipeline build snapshots/$(date +%F) ../app/public/well_proposals.json
   ```

   Compare the logged success rate with the game balance: a payout of three times the Well Cost roughly breaks even for blind drilling at a 30–40% success rate. If the rate drifts far from that, the budget and payout need retuning. The build stops with `LeakError` or `ContractError` rather than write a dataset that breaks the rules above.

3. Run the app's tests (`npm test` and `npm run test:smoke` in `app/`), then commit `app/public/well_proposals.json`. Its `dataset_version` (build date plus a content hash) is what Decision Records name, so the same content always gets the same version.

## Test

```bash
python -m pytest
```

```bash
mypy
```

Tests go only through the top-level function, `build_well_proposals`, using the hand-made fixture in `tests/fixtures/`.
