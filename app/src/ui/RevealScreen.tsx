import type { Action, CampaignState } from "../engine/campaign";
import { t } from "../i18n";
import { amount, signedAmount } from "./format";

type RevealState = Extract<CampaignState, { phase: "reveal" }>;

export function RevealScreen({ state, send }: { state: RevealState; send: (action: Action) => void }) {
  const { reveal } = state;
  const found = reveal.discovery_name ?? reveal.field_name;
  const levels = reveal.hydrocarbon_levels.map((l) => [l.formation, l.age].filter(Boolean).join(", "));

  return (
    <section className={`card reveal ${reveal.outcome.toLowerCase()}`} data-testid="reveal">
      <h2>{t("reveal.heading")}</h2>
      <p className="outcome">{t(`reveal.outcome.${reveal.outcome}`)}</p>
      <p>{t(reveal.decision === "Drill" ? "reveal.youDrilled" : "reveal.youDropped")}</p>
      <dl className="facts">
        <dt>{t("reveal.wellName")}</dt>
        <dd>{reveal.well_name}</dd>
        <dt>{t("reveal.operator")}</dt>
        <dd>{reveal.operator ?? t("dossier.unknown")}</dd>
        <dt>{t("reveal.year")}</dt>
        <dd>{reveal.year}</dd>
        {found && (
          <>
            <dt>{t("reveal.discovery")}</dt>
            <dd>{found}</dd>
          </>
        )}
        {levels.length > 0 && (
          <>
            <dt>{t("reveal.hydrocarbonLevels")}</dt>
            <dd>
              <ul>
                {levels.map((level, i) => (
                  <li key={i}>{level}</li>
                ))}
              </ul>
            </dd>
          </>
        )}
        <dt>{t("reveal.budgetChange")}</dt>
        <dd data-testid="budget-change">{signedAmount(reveal.budgetChange)}</dd>
      </dl>
      {reveal.drillWouldHaveChanged !== null && (
        <p className="would-have" data-testid="would-have">
          {reveal.drillWouldHaveChanged > 0
            ? t("reveal.wouldHaveFound", { name: found ?? reveal.well_name, amount: amount(reveal.drillWouldHaveChanged) })
            : t("reveal.wouldHaveLost", { amount: amount(-reveal.drillWouldHaveChanged) })}
        </p>
      )}
      <button type="button" className="primary" onClick={() => send({ type: "continue" })}>
        {t(state.campaignEndsAfterReveal ? "reveal.finish" : "reveal.next")}
      </button>
    </section>
  );
}
