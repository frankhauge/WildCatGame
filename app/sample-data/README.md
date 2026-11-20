# Sample data

A made-up FactPages snapshot for developing the app with a small, predictable dataset. Every well, operator, discovery and field name here is invented.

The app ships `../public/well_proposals.json` built from a real FactPages download (see [Refresh the dataset](../../pipeline/README.md#refresh-the-dataset)). To play the sample instead, build it over that file with the real pipeline, from the repo root, and don't commit the result:

```bash
python -m wildcat_pipeline build app/sample-data/snapshot app/public/well_proposals.json
```
