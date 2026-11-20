# Sample data

A made-up FactPages snapshot for developing and testing the app before the pipeline is run against a real FactPages download. Every well, operator, discovery and field name here is invented.

`../public/well_proposals.json` is built from it by the real pipeline, so it matches the dataset contract and passes the leak checks:

```bash
python -m wildcat_pipeline app/sample-data/snapshot app/public/well_proposals.json
```

Replace `app/public/well_proposals.json` with the pipeline's output from a real download to play real wells.
