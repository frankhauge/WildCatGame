# Wildcat app

The mobile-first web game: TypeScript, React and Vite, built to static files. Vocabulary: [CONTEXT.md](../CONTEXT.md). Information boundary: [ADR 0001](../docs/adr/0001-information-boundary-at-spud-date.md).

## Run

```bash
npm install
```

```bash
npm run dev
```

The app loads `public/well_proposals.json`, the pipeline's output from a real FactPages download. To refresh it, see [Refresh the dataset](../pipeline/README.md#refresh-the-dataset). A made-up sample snapshot is kept in [`sample-data/`](sample-data/README.md) for development.

## Build

```bash
npm run build
```

`dist/` can be served from any directory by any static file server.

## Test

```bash
npm run typecheck
```

```bash
npm test
```

```bash
npm run test:smoke
```

- `src/engine/campaign.test.ts` holds the scenario tests for the Campaign engine (`src/engine/campaign.ts`), a pure state machine with no UI or I/O. Engine tests go only through `createCampaignEngine`.
- `e2e/smoke.test.mjs` builds the app and plays one full Campaign in headless Chromium. It checks that no Reveal data appears before a decision and that the Sodir credit is visible. It uses the Playwright installed globally on the machine.

## Rules for the UI

- The UI only shows the engine's state and sends it actions. The engine leaves Reveal data out of the state until the Player has decided.
- All interface text comes from `src/i18n/en.json`, through `t()`.
- The Sodir credit under NLOD is always visible.
- The game never shows a chance of success.
