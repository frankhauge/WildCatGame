// The Campaign engine: a pure, deterministic state machine with no UI or I/O.
//
// The UI only shows CampaignState and sends Actions. Reveal data is kept out
// of the state until the Player has decided (ADR 0001), so the UI cannot show
// it early by mistake.

import type { Dataset, Dossier, Outcome, Reveal, WellProposal } from "../dataset";

export const CAMPAIGN_LENGTH = 10;
export const STARTING_BUDGET_IN_WELL_COSTS = 5;
export const STARTING_CONFIDENCE = 50;

export type Decision = "Drill" | "Drop";

export type Action =
  | { type: "setConfidence"; value: number }
  | { type: "drill" }
  | { type: "drop" }
  | { type: "continue" };

/** The Well Proposal being decided, without its Reveal. */
export interface CurrentWellProposal {
  id: string;
  dossier: Dossier;
  confidence: number;
  confidenceSet: boolean;
  /** When it was shown, by the clock, for the time taken to decide. */
  shownAt: number;
}

export interface RevealView extends Reveal {
  decision: Decision;
  /** How the Exploration Budget changed with this decision. */
  budgetChange: number;
  /** After a Drop: what a Drill would have earned or lost. Null after a Drill. */
  drillWouldHaveChanged: number | null;
}

export interface Tally {
  discoveries: number;
  dryWellsDrilled: number;
  dryWellsAvoided: number;
  discoveriesMissed: number;
}

interface CommonState {
  budget: number;
  startingBudget: number;
  wellCost: number;
  /** Well Proposals not yet decided, counting the one being decided. */
  wellProposalsLeft: number;
  tally: Tally;
}

export type CampaignState =
  | (CommonState & { phase: "deciding"; current: CurrentWellProposal })
  | (CommonState & { phase: "reveal"; reveal: RevealView; campaignEndsAfterReveal: boolean })
  | (CommonState & { phase: "ended"; netBudget: number });

export interface DecisionRecord {
  campaignId: string;
  wellProposalId: string;
  datasetVersion: string;
  hintsBought: string[];
  sectionsOpened: string[];
  timeTakenMs: number;
  confidence: number;
  decision: Decision;
  outcome: Outcome;
}

export interface Step {
  state: CampaignState;
  decisionRecords: DecisionRecord[];
  /** Set when the action was not allowed; the state is then unchanged. */
  rejected?: string;
}

export interface CampaignOptions {
  seed: number;
  /** Milliseconds since some fixed point, e.g. Date.now. */
  clock: () => number;
  campaignId: string;
}

export interface CampaignEngine {
  start(): Step;
  act(state: CampaignState, action: Action): Step;
}

export function createCampaignEngine(dataset: Dataset, options: CampaignOptions): CampaignEngine {
  const drawn = draw(dataset.well_proposals, Math.min(CAMPAIGN_LENGTH, dataset.well_proposals.length), options.seed);
  const wellCost = dataset.well_cost;

  // The Well Proposal being decided: the first one not yet decided.
  function proposalAt(state: CommonState): WellProposal {
    return drawn[drawn.length - state.wellProposalsLeft]!;
  }

  function deciding(common: CommonState): CampaignState {
    const proposal = proposalAt(common);
    return {
      ...common,
      phase: "deciding",
      current: {
        id: proposal.id,
        dossier: proposal.dossier,
        confidence: STARTING_CONFIDENCE,
        confidenceSet: false,
        shownAt: options.clock(),
      },
    };
  }

  function decide(state: CampaignState, decision: Decision): Step {
    if (state.phase !== "deciding") return reject(state, "Not deciding a Well Proposal");
    if (!state.current.confidenceSet) return reject(state, "Set Confidence first");
    if (decision === "Drill" && state.budget < wellCost) return reject(state, "Budget too low to Drill");

    const { reveal } = proposalAt(state);
    const discovery = reveal.outcome === "Discovery";
    const drillChange = discovery ? dataset.discovery_payout - wellCost : -wellCost;
    const budgetChange = decision === "Drill" ? drillChange : 0;
    const tally = { ...state.tally };
    if (decision === "Drill") {
      if (discovery) tally.discoveries++;
      else tally.dryWellsDrilled++;
    } else if (discovery) tally.discoveriesMissed++;
    else tally.dryWellsAvoided++;

    const { current, ...rest } = state;
    const common: CommonState = {
      ...rest,
      wellProposalsLeft: state.wellProposalsLeft - 1,
      budget: state.budget + budgetChange,
      tally,
    };
    const record: DecisionRecord = {
      campaignId: options.campaignId,
      wellProposalId: current.id,
      datasetVersion: dataset.dataset_version,
      hintsBought: [],
      sectionsOpened: [],
      timeTakenMs: options.clock() - current.shownAt,
      confidence: current.confidence,
      decision,
      outcome: reveal.outcome,
    };
    return {
      state: {
        ...common,
        phase: "reveal",
        campaignEndsAfterReveal: isOver(common),
        reveal: {
          ...reveal,
          decision,
          budgetChange,
          drillWouldHaveChanged: decision === "Drop" ? drillChange : null,
        },
      },
      decisionRecords: [record],
    };
  }

  // The Campaign ends after its last Well Proposal, or when the budget can't
  // pay for another Drill.
  function isOver(common: CommonState): boolean {
    return common.wellProposalsLeft === 0 || common.budget < wellCost;
  }

  return {
    start() {
      const startingBudget = STARTING_BUDGET_IN_WELL_COSTS * wellCost;
      const common: CommonState = {
        budget: startingBudget,
        startingBudget,
        wellCost,
        wellProposalsLeft: drawn.length,
        tally: { discoveries: 0, dryWellsDrilled: 0, dryWellsAvoided: 0, discoveriesMissed: 0 },
      };
      return { state: drawn.length > 0 ? deciding(common) : ended(common), decisionRecords: [] };
    },

    act(state, action) {
      switch (action.type) {
        case "setConfidence": {
          if (state.phase !== "deciding") return reject(state, "Not deciding a Well Proposal");
          if (!Number.isInteger(action.value) || action.value < 0 || action.value > 100) {
            return reject(state, "Confidence must be a whole percentage from 0 to 100");
          }
          const current = { ...state.current, confidence: action.value, confidenceSet: true };
          return { state: { ...state, current }, decisionRecords: [] };
        }
        case "drill":
          return decide(state, "Drill");
        case "drop":
          return decide(state, "Drop");
        case "continue": {
          if (state.phase !== "reveal") return reject(state, "No Reveal to continue from");
          const { reveal: _, campaignEndsAfterReveal: over, ...common } = state;
          return { state: over ? ended(common) : deciding(common), decisionRecords: [] };
        }
      }
    },
  };
}

function ended(common: CommonState): CampaignState {
  return { ...common, phase: "ended", netBudget: common.budget - common.startingBudget };
}

function reject(state: CampaignState, reason: string): Step {
  return { state, decisionRecords: [], rejected: reason };
}

/** Draw `count` Well Proposals at random without replacement. */
function draw(pool: WellProposal[], count: number, seed: number): WellProposal[] {
  const random = mulberry32(seed);
  const items = [...pool];
  // A partial Fisher-Yates shuffle: the first `count` items are the draw.
  for (let i = 0; i < count; i++) {
    const j = i + Math.floor(random() * (items.length - i));
    [items[i], items[j]] = [items[j]!, items[i]!];
  }
  return items.slice(0, count);
}

/** A small seeded pseudo-random generator, so a seed always gives the same Campaign. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
