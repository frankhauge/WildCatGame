# Decision Records as a training dataset

Player performance is tracked so it can later train a personal AI consultant. Each decision is therefore stored as a self-contained Decision Record: Dossier version, Hints bought, sections opened, time taken, Confidence, the Drill or Drop choice, the Outcome, and the Player Profile. Records are saved in Supabase in an EU region, with an anonymous ID that can later be linked to a signed-in account. Decisions are queued on the device and synced, so play works offline. We chose Supabase over Firebase or our own server because anonymous sign-in that upgrades to an account fits the play-first flow, and Postgres makes export for training straightforward.

## Consequences

- Training Consent is a separate, explicit opt-in from storing gameplay. It says in plain language what is collected and that it will be used to train an AI model. Without it, records are used only for the Player's own statistics. This is required by GDPR's separate-purpose rule.
- No personal data is stored unless the Player signs in. The Player Profile holds only discipline and experience level.
