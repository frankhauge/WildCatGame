# Information boundary at the spud date

Every Well Proposal is a real, already-drilled wildcat well, so its Outcome is public on Sodir's FactPages and anything dated after drilling started gives it away. We decided that everything shown before the Reveal (the Dossier, Hints, plain-language summaries and Hint prices) is built only from data that existed before the well's spud date. The well's own name, the real operator and the exact year are hidden until the Reveal, and only the decade is shown.

## Consequences

- The pipeline filters by date when it builds each Dossier. Nearby wells, discoveries, fields and seismic surveys count only if they existed before the spud date. Sidetracks are excluded because the main wellbore's result gives theirs away.
- Fields Sodir records while drilling a well, such as its total depth and the formation and age reached there, are not pre-spud data, even though they say nothing about the Outcome. Sodir records no planned target, so the Dossier shows none.
- LLM-written summaries get only pre-spud fields as input, and the output is checked automatically for leaked names and years, because the model may know from training what was found.
- Hint prices are set by how much each kind of Hint improves Outcome prediction across all wildcat wells, but neither those numbers nor any probability of success is ever shown to the Player. Confidence starts at a neutral 50%, and the game never suggests a value.
