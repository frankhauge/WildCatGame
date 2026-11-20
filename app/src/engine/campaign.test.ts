import { describe, expect, it } from "vitest";
import type { Dataset, Outcome, WellProposal } from "../dataset";
import { createCampaignEngine, type Action, type CampaignState, type Step } from "./campaign";

// Scenario tests at the Campaign engine seam (Seam 2): a list of actions,
// then assertions on the resulting state and the Decision Records emitted.

function wellProposal(n: number, outcome: Outcome): WellProposal {
  return {
    id: `WP${n.toString(16).padStart(12, "0")}`,
    dossier: {
      summary: `Summary ${n}`,
      operator: "Operator A",
      map_position: { lat: 60, lon: 2 },
      block: `${n}/1`,
      water_depth_m: 100,
      target_formation: "BRENT GP",
      target_age: "MIDDLE JURASSIC",
      decade: "1980s",
      geologist_view: {},
    },
    hints: {},
    reveal: {
      well_name: `${n}/1-1`,
      operator: `Operator ${n} AS`,
      year: 1980 + n,
      outcome,
      discovery_name: outcome === "Discovery" ? `FIELD${n}` : null,
      field_name: null,
      hydrocarbon_levels: outcome === "Discovery" ? [{ formation: "BRENT GP", age: "MIDDLE JURASSIC" }] : [],
    },
  };
}

function dataset(outcomes: Outcome[]): Dataset {
  return {
    dataset_version: "2026-11-20.abcdef12",
    build_date: "2026-11-20",
    source: { name: "Sodir FactPages", url: "", licence: "NLOD", licence_url: "", attribution: "" },
    well_cost: 100,
    discovery_payout: 300,
    hint_prices: {},
    well_proposals: outcomes.map((o, i) => wellProposal(i + 1, o)),
  };
}

const mixed = dataset([
  "Discovery", "Dry", "Dry", "Discovery", "Dry", "Dry",
  "Discovery", "Dry", "Dry", "Dry", "Discovery", "Dry",
]);

function fakeClock(start = 1_000_000) {
  let now = start;
  return { now: () => now, advance: (ms: number) => { now += ms; } };
}

function play(data: Dataset, actions: Action[], seed = 7) {
  const engine = createCampaignEngine(data, { seed, clock: fakeClock().now, campaignId: "C1" });
  const steps: Step[] = [engine.start()];
  for (const action of actions) steps.push(engine.act(steps.at(-1)!.state, action));
  return { engine, steps, state: steps.at(-1)!.state, last: steps.at(-1)! };
}

function drawnIds(data: Dataset, seed: number): string[] {
  const ids: string[] = [];
  const { engine } = play(data, [], seed);
  let state: CampaignState = engine.start().state;
  while (state.phase !== "ended") {
    if (state.phase === "deciding") {
      ids.push(state.current.id);
      state = engine.act(state, { type: "setConfidence", value: 50 }).state;
      state = engine.act(state, { type: "drop" }).state;
    } else {
      state = engine.act(state, { type: "continue" }).state;
    }
  }
  return ids;
}

describe("Campaign engine", () => {
  it("draws the same Campaign from the same seed", () => {
    expect(drawnIds(mixed, 42)).toEqual(drawnIds(mixed, 42));
    expect(drawnIds(mixed, 42)).not.toEqual(drawnIds(mixed, 43));
  });

  it("starts with five Well Costs and 10 Well Proposals left", () => {
    const { state } = play(mixed, []);
    expect(state.budget).toBe(500);
    expect(state.wellProposalsLeft).toBe(10);
    expect(state.phase).toBe("deciding");
  });

  it("counts a Well Proposal as done once it is decided", () => {
    const { steps } = play(mixed, [{ type: "setConfidence", value: 50 }, { type: "drop" }, { type: "continue" }]);
    expect(steps.map((s) => s.state.wellProposalsLeft)).toEqual([10, 10, 9, 9]);
  });

  it("starts each Well Proposal with Confidence at 50%, not yet set", () => {
    const { state } = play(mixed, []);
    expect(state.phase === "deciding" && state.current).toMatchObject({ confidence: 50, confidenceSet: false });
  });

  it("keeps the Reveal out of the state before a decision", () => {
    const { state } = play(mixed, [{ type: "setConfidence", value: 80 }]);
    const json = JSON.stringify(state);
    for (const p of mixed.well_proposals) {
      expect(json).not.toContain(p.reveal.well_name);
      expect(json).not.toContain(p.reveal.operator!);
    }
    expect(state).not.toHaveProperty("reveal");
  });

  it("locks Drill and Drop until Confidence is set", () => {
    const { steps } = play(mixed, [{ type: "drill" }, { type: "drop" }]);
    for (const step of steps.slice(1)) {
      expect(step.rejected).toBeDefined();
      expect(step.state).toBe(steps[0]!.state);
      expect(step.decisionRecords).toEqual([]);
    }
  });

  it("accepts 50% once Confidence has been set", () => {
    const { last } = play(mixed, [{ type: "setConfidence", value: 50 }, { type: "drop" }]);
    expect(last.rejected).toBeUndefined();
    expect(last.state.phase).toBe("reveal");
  });

  it("rejects a Confidence outside 0 to 100%", () => {
    const { last } = play(mixed, [{ type: "setConfidence", value: 101 }]);
    expect(last.rejected).toBeDefined();
  });

  it("takes one Well Cost for a Dry Drill and pays nothing", () => {
    const { state } = play(dataset(Array(12).fill("Dry")), [{ type: "setConfidence", value: 30 }, { type: "drill" }]);
    expect(state.budget).toBe(400);
    expect(state.phase === "reveal" && state.reveal).toMatchObject({ outcome: "Dry", decision: "Drill", budgetChange: -100 });
  });

  it("pays out three Well Costs for a Discovery, after the Drill's cost", () => {
    const { state } = play(dataset(Array(12).fill("Discovery")), [{ type: "setConfidence", value: 70 }, { type: "drill" }]);
    expect(state.budget).toBe(700);
    expect(state.phase === "reveal" && state.reveal).toMatchObject({ outcome: "Discovery", budgetChange: 200 });
  });

  it("shows the real well, operator, year and levels with hydrocarbons in the Reveal", () => {
    const data = dataset(Array(12).fill("Discovery"));
    const { steps, state } = play(data, [{ type: "setConfidence", value: 70 }, { type: "drill" }]);
    const first = steps[0]!.state;
    const proposal = data.well_proposals.find((p) => first.phase === "deciding" && p.id === first.current.id)!;
    expect(state.phase === "reveal" && state.reveal).toMatchObject(proposal.reveal);
  });

  it("shows after a Drop what a Drill would have earned", () => {
    const { state } = play(dataset(Array(12).fill("Discovery")), [{ type: "setConfidence", value: 20 }, { type: "drop" }]);
    expect(state.budget).toBe(500);
    expect(state.phase === "reveal" && state.reveal).toMatchObject({
      decision: "Drop",
      budgetChange: 0,
      drillWouldHaveChanged: 200,
    });
    expect(state.phase === "reveal" && state.reveal.discovery_name).toMatch(/^FIELD/);
  });

  it("shows after a Drop what a Drill would have lost", () => {
    const { state } = play(dataset(Array(12).fill("Dry")), [{ type: "setConfidence", value: 20 }, { type: "drop" }]);
    expect(state.phase === "reveal" && state.reveal).toMatchObject({ budgetChange: 0, drillWouldHaveChanged: -100 });
  });

  it("shows no Drop comparison after a Drill", () => {
    const { state } = play(mixed, [{ type: "setConfidence", value: 20 }, { type: "drill" }]);
    expect(state.phase === "reveal" && state.reveal.drillWouldHaveChanged).toBeNull();
  });

  it("ends after 10 Well Proposals with the final result", () => {
    const decideAll: Action[] = Array(10).fill([
      { type: "setConfidence", value: 50 },
      { type: "drop" },
      { type: "continue" },
    ]).flat();
    const { state, steps } = play(mixed, decideAll);
    expect(state).toMatchObject({ phase: "ended", wellProposalsLeft: 0, netBudget: 0, budget: 500 });
    const records = steps.flatMap((s) => s.decisionRecords);
    expect(records).toHaveLength(10);
    expect(new Set(records.map((r) => r.wellProposalId)).size).toBe(10);
  });

  it("counts Discoveries, Dry wells drilled, Dry wells avoided and Discoveries missed", () => {
    const decide = (type: "drill" | "drop"): Action[] => [
      { type: "setConfidence", value: 50 },
      { type },
      { type: "continue" },
    ];
    const data = dataset(["Discovery", "Dry", "Discovery", "Dry", "Discovery", "Dry", "Discovery", "Dry", "Discovery", "Dry"]);
    const { state, steps } = play(data, ["drill", "drop", "drill", "drop", "drill", "drop", "drill", "drop", "drill", "drop"].flatMap((t) => decide(t as "drill" | "drop")));
    const records = steps.flatMap((s) => s.decisionRecords);
    const count = (decision: string, outcome: string) =>
      records.filter((r) => r.decision === decision && r.outcome === outcome).length;
    expect(state.phase).toBe("ended");
    expect(state.tally).toEqual({
      discoveries: count("Drill", "Discovery"),
      dryWellsDrilled: count("Drill", "Dry"),
      dryWellsAvoided: count("Drop", "Dry"),
      discoveriesMissed: count("Drop", "Discovery"),
    });
    expect(state.phase === "ended" && state.netBudget).toBe(state.tally.discoveries * 200 - state.tally.dryWellsDrilled * 100);
  });

  it("ends after five Dry Drills in a row", () => {
    const drillDry: Action[] = [{ type: "setConfidence", value: 50 }, { type: "drill" }, { type: "continue" }];
    const { state } = play(dataset(Array(12).fill("Dry")), Array(5).fill(drillDry).flat());
    expect(state).toMatchObject({ phase: "ended", budget: 0, netBudget: -500, wellProposalsLeft: 5 });
    expect(state.tally.dryWellsDrilled).toBe(5);
  });

  it("ends early when the budget is below the Well Cost, even after some Drops", () => {
    const decide = (type: "drill" | "drop"): Action[] => [{ type: "setConfidence", value: 50 }, { type }, { type: "continue" }];
    const actions = [...decide("drop"), ...decide("drop"), ...Array(5).fill(decide("drill")).flat()];
    const { state, steps } = play(dataset(Array(12).fill("Dry")), actions);
    expect(state).toMatchObject({ phase: "ended", budget: 0, wellProposalsLeft: 3 });
    expect(steps.at(-2)!.state.phase).toBe("reveal");
  });

  it("tells the Reveal whether the Campaign ends after it", () => {
    const drillDry: Action[] = [{ type: "setConfidence", value: 50 }, { type: "drill" }, { type: "continue" }];
    const { steps } = play(dataset(Array(12).fill("Dry")), Array(5).fill(drillDry).flat());
    const reveals = steps.map((s) => s.state).filter((s) => s.phase === "reveal");
    expect(reveals.map((s) => s.campaignEndsAfterReveal)).toEqual([false, false, false, false, true]);
  });

  it("rejects actions after the Campaign has ended", () => {
    const drillDry: Action[] = [{ type: "setConfidence", value: 50 }, { type: "drill" }, { type: "continue" }];
    const { last } = play(dataset(Array(12).fill("Dry")), [...Array(5).fill(drillDry).flat(), { type: "setConfidence", value: 50 }, { type: "drill" }]);
    expect(last.rejected).toBeDefined();
    expect(last.state.phase).toBe("ended");
  });

  it("plays a shorter Campaign when the dataset has fewer than 10 Well Proposals", () => {
    const { state } = play(dataset(["Dry", "Discovery", "Dry"]), []);
    expect(state.wellProposalsLeft).toBe(3);
  });

  it("emits a Decision Record for each Drill or Drop, timed by the clock", () => {
    const clock = fakeClock();
    const engine = createCampaignEngine(mixed, { seed: 7, clock: clock.now, campaignId: "C1" });
    let { state } = engine.start();
    const id = state.phase === "deciding" ? state.current.id : "";
    clock.advance(12_500);
    state = engine.act(state, { type: "setConfidence", value: 35 }).state;
    const step = engine.act(state, { type: "drill" });
    const outcome = mixed.well_proposals.find((p) => p.id === id)!.reveal.outcome;
    expect(step.decisionRecords).toEqual([
      {
        campaignId: "C1",
        wellProposalId: id,
        datasetVersion: "2026-11-20.abcdef12",
        hintsBought: [],
        sectionsOpened: [],
        timeTakenMs: 12_500,
        confidence: 35,
        decision: "Drill",
        outcome,
      },
    ]);
    clock.advance(3_000);
    state = engine.act(step.state, { type: "continue" }).state;
    clock.advance(4_000);
    state = engine.act(state, { type: "setConfidence", value: 50 }).state;
    expect(engine.act(state, { type: "drop" }).decisionRecords[0]!.timeTakenMs).toBe(4_000);
  });
});
