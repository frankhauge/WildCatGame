# Information boundary at the spud date

Every Prospect is a real, already-drilled wildcat well, so its Outcome is public on Sodir's FactPages and anything dated after drilling started gives it away. We decided that everything shown before the Reveal (the Dossier, Hints, plain-language summaries and Hint prices) is built only from data that existed before the well's spud date. The well's own name, the real operator and the exact year are hidden until the Reveal, and only the decade is shown.

## Consequences

- The pipeline filters by date when it builds each Dossier. Nearby wells, discoveries, fields and seismic surveys count only if they existed before the spud date. Sidetracks are excluded because the main wellbore's result gives theirs away.
- LLM-written summaries get only pre-spud fields as input, and the output is checked automatically for leaked names and years, because the model may know from training what was found.
- Hint prices are set by how much each kind of Hint improves Outcome prediction across all wildcat wells, but neither those numbers nor any probability of success is ever shown to the Player. Confidence starts at a neutral 50%, and the game never suggests a value.
