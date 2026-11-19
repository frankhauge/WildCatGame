# Pipeline test fixtures

`snapshot/` is a small, hand-made FactPages snapshot. Names and operators are made up. Column names follow Sodir's FactPages CSV exports, cut down to the columns the pipeline reads.

| Wellbore | Case |
|---|---|
| 34/10-1 | Discovery (oil); its discovery and field TROLLHAUGEN are dated after the spud date |
| 2/4-3 | Dry well |
| 25/7-1 | Well with only shows (counts as Dry) |
| 34/10-2 | Appraisal well (not eligible) |
| 15/9-19 S | Main wellbore whose name contains its later discovery's name, 15/9-19 |
| 15/9-19 A | Sidetrack (not eligible) |
| 7120/12-1 | Frontier well in the Barents Sea, far from any earlier well (eligible) |
| 6/3-1 | Result not known (not eligible) |

`discovery.csv` holds data dated after the spud dates (discovery years, production status) that must never appear outside a Prospect's Reveal.
