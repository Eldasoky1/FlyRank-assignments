export type Category = "billing" | "technical" | "account" | "sales" | "other";

/** The AI's decision — which branch the ticket should flow down. */
export interface Intent {
  category: Category;
  confidence: number;
  /** Short human-readable reason for the chosen branch. */
  reason: string;
}

export type StepStatus = "pending" | "running" | "done";

/** One unit of work inside a branch. Mirrors an Inngest `step.run`. */
export interface FlowStep {
  id: string;
  label: string;
  detail: string;
  status: StepStatus;
}

export interface BranchDefinition {
  category: Category;
  /** Keywords that bias the router toward this branch. */
  keywords: string[];
  /** Fallback confidence when no explicit keyword matched. */
  baseConfidence: number;
  /** The ordered steps this branch executes. */
  steps: Omit<FlowStep, "status" | "id">[];
}
