# Wildcat

A mobile-first web game where players decide whether to drill real, historical exploration targets on the Norwegian Continental Shelf, judged against the actual outcome recorded in Sodir's FactPages.

## Language

### The game

**Wildcat**:
The name of the game. In prose, always write "the game" or "Wildcat" (capitalised) to keep it apart from a **wildcat well**.

**Well Proposal**:
A historical **wildcat well** as it was proposed before its spud date, presented to the player with its outcome hidden, as a decision to make. It targets one or more **Prospects**.
_Avoid_: Card, well, target, lead, Prospect

**Campaign**:
One playthrough: a sequence of **Well Proposals** played against a fixed **Exploration Budget**.
_Avoid_: Game, round, session, level

Well Proposals in a Campaign are drawn at random from all eligible wildcat wells, regardless of era or region.

**Exploration Budget**:
The funds a player has at the start of a **Campaign**: five **Well Costs**, so at most five **Dry** Drills in a row, fewer if **Hints** are bought. Each **Drill** and **Hint** costs money from it.
_Avoid_: Money, wallet, coins

**Drill**:
The player's decision to spend budget to drill a **Well Proposal**, testing every **Prospect** it targets.

**Drop**:
The player's decision to pass on a **Well Proposal** without spending budget.
_Avoid_: Skip, pass, relinquish

**Dossier**:
Everything the player sees about a **Well Proposal** before deciding, built only from data that existed before the well's spud date.
_Avoid_: Brief, info, card details

**Geologist View**:
The expanded layer of a **Dossier** that shows the raw Sodir fields behind the plain-language summary.
_Avoid_: Expert mode, advanced mode

**Outcome**:
Either **Discovery** or **Dry**, taken from Sodir's record of the well. A well is a Discovery if any **Prospect** it targets holds hydrocarbons; a well with only shows counts as **Dry**.

**Hint**:
A purchasable piece of extra **Dossier** information, built only from data from before the spud date. Each kind of Hint has its own price, paid from the **Exploration Budget**.
_Avoid_: Clue, tip, power-up

**Well Cost**:
The fixed amount a **Drill** takes from the **Exploration Budget**.

**Discovery Payout**:
The fixed amount a **Drill** returns when the **Outcome** is **Discovery**: three times the **Well Cost**.

**Reveal**:
The moment after a decision when the real well, its operator, year and **Outcome** are shown, with the levels where hydrocarbons were found. After a **Drop**, the Reveal shows what a Drill would have earned or lost.

### The player and their data

**Player**:
Anyone playing, identified by an anonymous ID that can later be linked to a signed-in account.
_Avoid_: User, account, customer

**Player Profile**:
A **Player**'s self-reported discipline (geologist, geophysicist, reservoir engineer, production engineer, or other) and experience level.

**Decision Record**:
A self-contained log entry for one decision on one **Well Proposal**: what the **Player** saw, which **Hints** they bought, their **Confidence**, their choice and the **Outcome**.
_Avoid_: Answer, event, log

**Confidence**:
The **Player**'s own estimate of how likely a **Well Proposal** is to be a **Discovery**, set before every decision. It starts at 50%, and the Player must touch it before they can Drill or Drop; leaving it at 50% is a valid answer. The game never suggests a value.

**Training Consent**:
A **Player**'s explicit, informed permission for their **Decision Records** to be used to train the AI consultant. It is separate from storing gameplay.

### Source domain (Sodir)

**Sodir**:
Sokkeldirektoratet, the Norwegian Offshore Directorate. It publishes the FactPages, the game's only source of truth.
_Avoid_: NPD (former name), the directorate

**Wildcat well**:
A wellbore whose Sodir purpose is WILDCAT: the first well drilled into an untested structure. Appraisal wells are not wildcat wells.
_Avoid_: Exploration well (broader: it includes appraisal)

### Geology

**Prospect**:
A mapped, untested trap at one reservoir level: an area on the map that may hold hydrocarbons. Several wells can target one Prospect, and one well can target several Prospects, for example a shallow Brent Prospect and a deeper Statfjord Prospect.
_Avoid_: Structure, target, lead (a less mature idea than a Prospect)
