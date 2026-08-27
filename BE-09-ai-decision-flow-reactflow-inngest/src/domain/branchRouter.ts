import type { BranchDefinition, Category, Intent } from "./types";

/**
 * The branches the decision flow can route to. Each lists the keywords the
 * router uses to decide. This is the same data the Inngest step function uses.
 */
export const BRANCHES: BranchDefinition[] = [
  {
    category: "billing",
    keywords: ["charge", "charged", "charging", "refund", "billed", "billing", "invoice", "price", "payment", "fee", "subscription cost"],
    baseConfidence: 0.71,
    steps: [
      { label: "Look up subscription", detail: "Fetch the user's plan and recent charges." },
      { label: "Compute refund", detail: "Calculate the amount to credit back." },
      { label: "Issue refund", detail: "Credit the user's original payment method." },
    ],
  },
  {
    category: "technical",
    keywords: ["error", "crash", "crashing", "bug", "broken", "not loading", "failed", "500", "freeze", "cant access", "cannot access", "login error", "slow"],
    baseConfidence: 0.7,
    steps: [
      { label: "Gather logs", detail: "Pull recent app/API logs for the session." },
      { label: "Run diagnostics", detail: "Replay the failing request against the stack." },
      { label: "Propose fix", detail: "Suggest a patch or workaround to the engineer." },
    ],
  },
  {
    category: "account",
    keywords: ["reset password", "password", "forgot", "locked out", "username", "2fa", "two-factor", "email change", "account access", "verify"],
    baseConfidence: 0.68,
    steps: [
      { label: "Verify identity", detail: "Confirm ownership via email/SMS OTP." },
      { label: "Reset access", detail: "Regenerate credentials or unlock the account." },
      { label: "Notify user", detail: "Send confirmation and next steps." },
    ],
  },
  {
    category: "sales",
    keywords: ["plan", "upgrade", "price quote", "pricing", "sign up", "buy", "purchase", "discount", "enterprise", "trial", "demo"],
    baseConfidence: 0.66,
    steps: [
      { label: "Recommend plan", detail: "Pick the plan that fits the user's needs." },
      { label: "Build offer", detail: "Assemble pricing and a promo if eligible." },
      { label: "Send offer", detail: "Email the tailored proposal." },
    ],
  },
  {
    category: "other",
    keywords: [],
    baseConfidence: 0.4,
    steps: [
      { label: "Assign human agent", detail: "Route to the next available specialist." },
      { label: "Escalate", detail: "Flag for manual review if urgent." },
    ],
  },
];

/**
 * The AI decision: classify a raw support message into a branch.
 *
 * This is a lightweight, interpretable router (deterministic, fully testable).
 * In production you swap `classifyMessage` for a real LLM call; the rest of
 * the flow (React Flow rendering + Inngest orchestration) is unchanged.
 */
export function classifyMessage(message: string): Intent {
  const text = message.toLowerCase();
  let best: { branch: BranchDefinition; hits: number } | null = null;

  for (const branch of BRANCHES) {
    if (branch.keywords.length === 0) continue;
    const hits = branch.keywords.filter((k) => text.includes(k)).length;
    if (hits > 0 && (!best || hits > best.hits)) best = { branch, hits };
  }

  if (!best) {
    const other = BRANCHES.find((b) => b.category === "other")!;
    return {
      category: "other",
      confidence: other.baseConfidence,
      reason: "No intent keywords matched; routing to a human.",
    };
  }

  // Confidence rises with how many keywords matched (capped at 0.98).
  const confidence = Math.min(0.98, best.branch.baseConfidence + 0.07 * best.hits);
  return {
    category: best.branch.category,
    confidence: Number(confidence.toFixed(2)),
    reason: `Matched ${best.hits} intent keyword(s): "${best.branch.keywords
      .filter((k) => text.includes(k))
      .slice(0, 3)
      .join(", ")}".`,
  };
}

export function branchSteps(category: Category): BranchDefinition["steps"] {
  const branch = BRANCHES.find((b) => b.category === category)!;
  return branch.steps;
}
