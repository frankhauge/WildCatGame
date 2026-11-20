// The Well Proposals dataset: the only interface between the pipeline and the
// app. Mirrors pipeline/src/wildcat_pipeline/well_proposals.schema.json.

export type Outcome = "Discovery" | "Dry";

export interface Dataset {
  dataset_version: string;
  build_date: string;
  source: {
    name: string;
    url: string;
    licence: "NLOD";
    licence_url: string;
    attribution: string;
  };
  well_cost: number;
  discovery_payout: number;
  hint_prices: Record<string, number>;
  well_proposals: WellProposal[];
}

export interface WellProposal {
  id: string;
  dossier: Dossier;
  hints: Record<string, unknown>;
  // Must never be shown before a decision (ADR 0001).
  reveal: Reveal;
}

export interface Dossier {
  summary: string;
  operator: "Operator A";
  map_position: { lat: number | null; lon: number | null };
  block: string;
  water_depth_m: number | null;
  decade: string;
  geologist_view: Record<string, string | number | null>;
}

export interface Reveal {
  well_name: string;
  operator: string | null;
  year: number;
  outcome: Outcome;
  discovery_name: string | null;
  field_name: string | null;
  hydrocarbon_levels: { formation: string | null; age: string | null }[];
}
