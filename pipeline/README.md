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

Each Dossier's plain-language summary is written by Claude (`ClaudeSummaryWriter`), which needs an Anthropic API key in `ANTHROPIC_API_KEY` (or an `ant auth login` profile). Claude is given only the Dossier's pre-spud fields. Every summary goes through the leak guard as soon as it is written, because the model may know from training what a well found: a summary that leaks, or that Claude fails to write, is asked for again, up to three attempts in all. A summary that still leaks fails the build with `LeakError`; one that still cannot be written is flagged in the log and left empty. Add `--no-summaries` to build without asking Claude.

Each build with summaries also writes `reviews/summaries-<dataset_version>.md` (`--reviews` picks another directory): 20 summaries drawn at random, each beside its Reveal, and every flagged well. The leak guard catches names and years, not a summary that gives the Outcome away in other words, so a person reads it. `reviews/` is not committed: it shows Reveals.

The build fails with `ContractError` if the output does not match [`well_proposals.schema.json`](src/wildcat_pipeline/well_proposals.schema.json), and with `LeakError` if anything outside a Well Proposal's Reveal names a well, discovery, field or operator, gives an exact year, or names anything dated on or after the spud date.

## Refresh the dataset

Run these by hand from `pipeline/` whenever new wells should come into the game. No code changes are needed.

1. Download a fresh snapshot into a new directory named after today's date:

   ```bash
   python -m wildcat_pipeline download snapshots/$(date +%F)
   ```

   This saves the tables the game is built from (the build reads only the first two so far; the rest are for the Hints and the map): wellbores, discoveries, fields, licences, seismic surveys (`survey.csv`) and block outlines (`blkArea.csv`, WKT polygons). `snapshot.json` records when and from which URL each file came. It takes a minute or two. A snapshot is never overwritten, and a failed download leaves nothing behind. `snapshots/` is not committed.

2. Build the dataset the app ships:

   ```bash
   python -m wildcat_pipeline build snapshots/$(date +%F) ../app/public/well_proposals.json
   ```

   Read the summary review it writes to `reviews/`. If a summary gives the Outcome away or reads badly, tighten the instructions in `claude_writer.py` and build again. Then compare the logged success rate with the game balance: a payout of three times the Well Cost roughly breaks even for blind drilling at a 30–40% success rate. If the rate drifts far from that, the budget and payout need retuning. The build stops with `LeakError` or `ContractError` rather than write a dataset that breaks the rules above.

3. Run the app's tests (`npm test` and `npm run test:smoke` in `app/`), then commit `app/public/well_proposals.json`. Its `dataset_version` (build date plus a hash of the content) is what Decision Records name: it changes whenever the content changes, so every refresh gives a new version.

## Test

```bash
python -m pytest
```

```bash
mypy
```

Tests go only through the top-level functions: `build_well_proposals`, using the hand-made fixture in `tests/fixtures/` and fake summary writers; `summary_review`; `download_snapshot`, with a fake fetch instead of the network; and `ClaudeSummaryWriter`, with a fake client instead of the Claude API.
