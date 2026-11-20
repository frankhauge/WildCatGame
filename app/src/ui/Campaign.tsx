import { useState } from "react";
import type { Dataset } from "../dataset";
import { createCampaignEngine, type Action, type CampaignEngine, type CampaignState, type DecisionRecord } from "../engine/campaign";
import { t } from "../i18n";
import { Deciding } from "./Deciding";
import { amount } from "./format";
import { Result } from "./Result";
import { RevealScreen } from "./RevealScreen";

// Decision Records are stored and synced in a later release; for now they are
// only handed here.
function emit(_records: DecisionRecord[]): void {}

function newCampaign(dataset: Dataset): { engine: CampaignEngine; state: CampaignState } {
  const seed = crypto.getRandomValues(new Uint32Array(1))[0]!;
  const engine = createCampaignEngine(dataset, { seed, clock: Date.now, campaignId: crypto.randomUUID() });
  return { engine, state: engine.start().state };
}

/** Shows the Campaign engine's state and sends it the Player's actions. */
export function Campaign({ dataset }: { dataset: Dataset }) {
  const [{ engine, state }, setCampaign] = useState(() => newCampaign(dataset));

  function send(action: Action) {
    const step = engine.act(state, action);
    emit(step.decisionRecords);
    setCampaign({ engine, state: step.state });
  }

  return (
    <>
      <dl className="status" aria-live="polite">
        <div>
          <dt>{t("status.budget")}</dt>
          <dd data-testid="budget">{amount(state.budget)}</dd>
        </div>
        <div>
          <dt>{t("status.wellProposalsLeft")}</dt>
          <dd data-testid="well-proposals-left">{state.wellProposalsLeft}</dd>
        </div>
      </dl>
      {state.phase === "deciding" && <Deciding key={state.current.id} state={state} send={send} />}
      {state.phase === "reveal" && <RevealScreen state={state} send={send} />}
      {state.phase === "ended" && <Result state={state} playAgain={() => setCampaign(newCampaign(dataset))} />}
    </>
  );
}
