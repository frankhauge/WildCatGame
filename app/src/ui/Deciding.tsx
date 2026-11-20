import type { CampaignState, Action } from "../engine/campaign";
import { t } from "../i18n";
import { amount } from "./format";

type DecidingState = Extract<CampaignState, { phase: "deciding" }>;

export function Deciding({ state, send }: { state: DecidingState; send: (action: Action) => void }) {
  const { dossier, confidence, confidenceSet } = state.current;
  const unknown = t("dossier.unknown");
  const setConfidence = (value: number) => send({ type: "setConfidence", value });

  return (
    <section className="card" data-testid="dossier">
      <h2>{t("dossier.heading")}</h2>
      {dossier.summary && (
        <p className="summary" data-testid="dossier-summary">
          {dossier.summary}
        </p>
      )}
      <dl className="facts">
        <dt>{t("dossier.block")}</dt>
        <dd>{dossier.block}</dd>
        <dt>{t("dossier.operator")}</dt>
        <dd>{dossier.operator}</dd>
        <dt>{t("dossier.decade")}</dt>
        <dd>{dossier.decade}</dd>
        <dt>{t("dossier.waterDepth")}</dt>
        <dd>{dossier.water_depth_m == null ? unknown : t("dossier.waterDepthValue", { metres: amount(dossier.water_depth_m) })}</dd>
        <dt>{t("dossier.targetFormation")}</dt>
        <dd>{dossier.target_formation ?? unknown}</dd>
        <dt>{t("dossier.targetAge")}</dt>
        <dd>{dossier.target_age ?? unknown}</dd>
      </dl>

      <label className="confidence">
        <span>{t("confidence.label")}</span>
        <output data-testid="confidence">{t("confidence.value", { percent: confidence })}</output>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={confidence}
          data-testid="confidence-slider"
          onChange={(e) => setConfidence(Number(e.currentTarget.value))}
          // Tapping the slider without moving it confirms the current value,
          // so 50% can be a deliberate answer.
          onPointerUp={(e) => setConfidence(Number(e.currentTarget.value))}
          onKeyUp={(e) => {
            if (e.key === "Enter" || e.key === " ") setConfidence(Number(e.currentTarget.value));
          }}
        />
      </label>
      {!confidenceSet && <p className="hint">{t("confidence.prompt")}</p>}

      <div className="decisions">
        <button
          type="button"
          className="drill"
          disabled={!confidenceSet}
          onClick={() => send({ type: "drill" })}
        >
          {t("decision.drill")} <small>{t("decision.drillCost", { amount: amount(state.wellCost) })}</small>
        </button>
        <button type="button" className="drop" disabled={!confidenceSet} onClick={() => send({ type: "drop" })}>
          {t("decision.drop")} <small>{t("decision.dropCost")}</small>
        </button>
      </div>
    </section>
  );
}
