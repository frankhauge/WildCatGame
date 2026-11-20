# Wildcat: design summary (first release)

Result of the design grilling of 2026-11-19. Vocabulary: [CONTEXT.md](../CONTEXT.md). Key decisions: [ADR 0001](adr/0001-information-boundary-at-spud-date.md), [ADR 0002](adr/0002-decision-records-as-training-dataset.md).

## Concept

The player is given real, already-drilled **wildcat wells** on the Norwegian Continental Shelf as **Well Proposals**, with the result hidden, and decides to **Drill** or **Drop**. The **Reveal** then shows what really happened. All facts come from Sodir's FactPages (open data under the NLOD licence; the app must credit Sodir as the source).

Audience: both industry professionals and curious non-experts. One layered interface serves both: a plain-language **Dossier** first, with a free **Geologist View** that shows the raw Sodir fields behind it.

## Campaign rules

- A **Campaign** has 10 Well Proposals drawn at random from all eligible wildcat wells. The real success rate is kept, with no balancing between Discoveries and Dry wells.
- **Exploration Budget**: 5 × Well Cost. One shared budget pays for both Drills and Hints.
- Scoring is binary.

  | | Discovery | Dry (shows count as Dry) |
  |---|---|---|
  | Drill | +3 × Well Cost | −1 × Well Cost |
  | Drop | 0 | 0 |

- A Campaign ends after 10 Well Proposals, or earlier if the budget can't pay for another Drill. If the dataset holds fewer than 10 Well Proposals, the Campaign plays all of them.
- After a Drop, the Reveal shows what a Drill would have earned or lost.
- The final result shows the net budget, the final budget, Discoveries, Dry wells drilled, Dry wells avoided and Discoveries missed, with a button to play another Campaign.
- **Confidence** is a slider that starts at 50%. The player must touch it before Drill or Drop become available, and 50% is an allowed answer. The game never suggests a chance of success.

## Information boundary (ADR 0001)

Everything shown before the Reveal is built from data that existed **before the spud date**. Before the Reveal:

- the well's name is hidden
- the operator is shown as "Operator A"
- only the decade is shown, not the year

The **free baseline Dossier** contains:

- map position and block
- water depth
- decade
- an LLM-written plain-language summary, checked automatically for leaked names and years

**Hints** are bought from the budget:

| Hint | What it tells you |
|---|---|
| Licence history | Award round, licence age, earlier wells on the licence |
| Regional analogues | How many earlier nearby wells found hydrocarbons, grouped by the formations they found them in (Sodir records no planned target to match on). Frontier wells show "no analogues: frontier acreage". |
| Seismic coverage | Which 2D or 3D surveys covered the area before the spud date |
| Nearest discovery | Distance to and type of the closest earlier discovery |

Hint prices are set from **value of information**. The pipeline measures how much each kind of Hint improves prediction of the Outcome across all wildcat wells, and scales the prices so the most useful Hint costs about 0.2 × Well Cost. The underlying numbers are never shown to the player.

## Eligible wells

A well is eligible if all of these hold:

- its Sodir purpose is WILDCAT
- it is a main wellbore (no sidetracks)
- its result is known

Frontier wells, with no earlier wells nearby, are included.

## Player and data (ADR 0002)

- **Identity:** the player starts with an anonymous ID and can later sign in (sign-in is not in the first release).
- **Player Profile:** asked after the first Campaign, and can be skipped. It records discipline and experience level:
  - Discipline: geologist, geophysicist, reservoir engineer, production engineer, other industry, not in the industry.
  - Experience: student, 0–5 years, 5–15 years, 15+ years, not applicable.
- **Decision Record:** one per decision. It holds:
  - player, Campaign, Well Proposal and Dossier version
  - Hints bought
  - sections opened
  - time taken
  - Confidence
  - Drill or Drop
  - Outcome
- **Training Consent:** a separate, explicit opt-in with a plain-language explanation of what is collected and that it is used to train an AI model. Without consent, records are used only for the player's own statistics.
- **Storage:** Supabase in an EU region. Records are queued on the device and synced, so play works offline.

## Architecture

- `pipeline/`: Python with pandas, run by hand. It pulls the FactPages data, applies the information boundary, computes Hint prices and writes summaries, and produces a versioned `well_proposals.json`. That file is the only interface between the pipeline and the app.
- `app/`: installable mobile-first web app in TypeScript, React and Vite, with a map built on MapLibre and Sodir's block outlines. Interface text lives in translation files: English first, Norwegian (bokmål) later.

## Not in the first release

Sign-in accounts, the AI consultant, leaderboards, daily shared Campaigns, the Norwegian translation, payouts based on discovery size.
