# Wildcat

A mobile-first web game where players decide whether to drill real, historical exploration targets on the Norwegian Continental Shelf, judged against the actual outcome recorded in Sodir's FactPages.

## Language

### The game

**Wildcat**:
The name of the game. In prose, always write "the game" or "Wildcat" (capitalised) to keep it apart from a **wildcat well**.

**Prospect**:
A historical **wildcat well** presented to the player with its outcome hidden, as a decision to make.
_Avoid_: Card, well, target, lead

**Campaign**:
One playthrough: a sequence of **Prospects** played against a fixed **Exploration Budget**.
_Avoid_: Game, round, session, level

Prospects in a Campaign are drawn at random from all eligible wildcat wells, regardless of era or region.

**Exploration Budget**:
The funds a player has at the start of a **Campaign**. Each **Drill** costs money from it.
_Avoid_: Money, wallet, coins

**Drill**:
The player's decision to spend budget to test a **Prospect**.

**Drop**:
The player's decision to pass on a **Prospect** without spending budget.
_Avoid_: Skip, pass, relinquish

**Dossier**:
Everything the player sees about a **Prospect** before deciding, built only from data that existed before the well's spud date.
_Avoid_: Brief, info, card details

**Geologist View**:
The expanded layer of a **Dossier** that shows the raw Sodir fields behind the plain-language summary.
_Avoid_: Expert mode, advanced mode

**Outcome**:
Either **Discovery** or **Dry**, taken from Sodir's record of the well. A well with only shows counts as **Dry**.

**Hint**:
A purchasable piece of extra **Dossier** information, built only from data from before the spud date. Each kind of Hint has its own price, paid from the **Exploration Budget**.
_Avoid_: Clue, tip, power-up

**Well Cost**:
The fixed amount a **Drill** takes from the **Exploration Budget**.

**Discovery Payout**:
The fixed amount a **Drill** returns when the **Outcome** is **Discovery**: three times the **Well Cost**.

**Reveal**:
The moment after a decision when the real well, its operator, year and outcome are shown. After a **Drop**, the Reveal shows what a Drill would have earned or lost.

### The player and their data

**Player**:
Anyone playing, identified by an anonymous ID that can later be linked to a signed-in account.
_Avoid_: User, account, customer

**Player Profile**:
A **Player**'s self-reported discipline (geologist, geophysicist, reservoir engineer, production engineer, or other) and experience level.

**Decision Record**:
A self-contained log entry for one decision on one **Prospect**: what the **Player** saw, which **Hints** they bought, their **Confidence**, their choice and the **Outcome**.
_Avoid_: Answer, event, log

**Confidence**:
The **Player**'s optional estimate of how likely a **Prospect** is to be a **Discovery**, given before deciding.

**Training Consent**:
A **Player**'s explicit, informed permission for their **Decision Records** to be used to train the AI consultant. It is separate from storing gameplay.

### Source domain (Sodir)

**Sodir**:
Sokkeldirektoratet, the Norwegian Offshore Directorate. It publishes the FactPages, the game's only source of truth.
_Avoid_: NPD (former name), the directorate

**Wildcat well**:
A wellbore whose Sodir purpose is WILDCAT: the first well drilled into an untested structure. Appraisal wells are not wildcat wells.
_Avoid_: Exploration well (broader: it includes appraisal)
