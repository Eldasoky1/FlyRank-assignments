import { classifyMessage, branchSteps } from "../domain/branchRouter";
import type { FlowStep, Intent } from "../domain/types";

/**
 * Offline runner that executes the SAME step sequence as the Inngest
 * `routeTicket` function, without needing an Inngest server or the cloud.
 *
 * This is what powers the React UI (and the tests). It emits each step with a
 * status transition so the React Flow canvas can render the flow in real time.
 */
export interface RunResult {
  intent: Intent;
  steps: FlowStep[];
}

export async function runDecisionFlow(
  message: string,
  opts: {
    onIntent?: (intent: Intent) => void;
    onStep?: (step: FlowStep, all: FlowStep[]) => void;
    delayMs?: number;
  } = {},
): Promise<RunResult> {
  const { onIntent, onStep, delayMs = 350 } = opts;
  // Step 1 — detect intent (the AI decision)
  const intent = classifyMessage(message);
  onIntent?.(intent);

  // Step 2..n — expand the branch and mark each action done, one at a time
  const actions = branchSteps(intent.category);
  const steps: FlowStep[] = actions.map((a) => ({
    id: a.label,
    label: a.label,
    detail: a.detail,
    status: "pending",
  }));

  for (const s of steps) {
    s.status = "running";
    onStep?.({ ...s }, steps);
    await sleep(delayMs);
    s.status = "done";
    onStep?.({ ...s }, steps);
  }

  return { intent, steps };
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
