# Pipeline test fixtures

`snapshot/` is a small, hand-made FactPages snapshot. Names and operators are made up. Column names follow Sodir's FactPages CSV exports, cut down to the columns the pipeline reads.

| Wellbore | Case |
|---|---|
| 34/10-1 | Discovery (oil) with hydrocarbons at two levels, Brent and Statfjord; its discovery and field TROLLHAUGEN are dated after the spud date |
| 2/4-3 | Dry well |
| 25/7-1 | Well with only shows (counts as Dry) |
| 34/10-2 | Appraisal well (not eligible) |
| 15/9-19 | Main wellbore whose name contains its later discovery's name, 15/9-19 |
| 15/9-19 S | Sidetrack (not eligible) |
| 7120/12-1 | Frontier well in the Barents Sea, far from any earlier well (eligible) |
| 30/6-5 | Discovery with content OIL/GAS/CONDENSATE |
| 6/3-1 | Result not known (not eligible) |

`discovery.csv` holds data dated after the spud dates (discovery years, production status) that must never appear outside a Well Proposal's Reveal. Also:

- ISBJELLET was found in 1981 by 7120/12-1, spudded in June 1981. It is earlier knowledge for 15/9-19, spudded in November 1981.
- HAVBRIS was found in 1985 by a wellbore that is not in the snapshot, so only its year dates it. A discovery in the same year as the spud date counts as earlier knowledge for 25/7-1 (1985).
- TOR, found in 1990, shares its name with the Tor Formation, where 2/4-3 reached total depth. Naming a formation is not a leak.
