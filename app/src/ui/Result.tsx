import type { CampaignState } from "../engine/campaign";
import { t } from "../i18n";
import { amount, signedAmount } from "./format";

type EndedState = Extract<CampaignState, { phase: "ended" }>;

export function Result({ state, playAgain }: { state: EndedState; playAgain: () => void }) {
  const { tally } = state;
  return (
    <section className="card" data-testid="result">
      <h2>{t("result.heading")}</h2>
      <dl className="facts">
        <dt>{t("result.netBudget")}</dt>
        <dd data-testid="net-budget">{signedAmount(state.netBudget)}</dd>
        <dt>{t("result.finalBudget")}</dt>
        <dd>{amount(state.budget)}</dd>
        <dt>{t("result.discoveries")}</dt>
        <dd>{tally.discoveries}</dd>
        <dt>{t("result.dryWellsDrilled")}</dt>
        <dd>{tally.dryWellsDrilled}</dd>
        <dt>{t("result.dryWellsAvoided")}</dt>
        <dd>{tally.dryWellsAvoided}</dd>
        <dt>{t("result.discoveriesMissed")}</dt>
        <dd>{tally.discoveriesMissed}</dd>
      </dl>
      <button type="button" className="primary" onClick={playAgain}>
        {t("result.playAgain")}
      </button>
    </section>
  );
}
