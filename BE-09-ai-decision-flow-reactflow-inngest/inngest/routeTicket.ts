import { classifyMessage, branchSteps } from "../src/domain/branchRouter";
import { inngest } from "./client";

export const ROUTE_TICKET_EVENT = "ticket/new";

export interface TicketNewEvent {
  name: typeof ROUTE_TICKET_EVENT;
  data: { message: string };
}

/**
 * The decision workflow, defined as an Inngest step function.
 *
 * Sequence (each `step.run` is a durable, replayable unit of work):
 *   1. detect-intent  -> the AI decides which branch the ticket belongs to
 *   2. expand-branch  -> load the ordered actions for that branch
 *   3. execute:<step> -> run each branch action as its own idempotent step
 *
 * Durable execution means every completed step is checkpointed: if the
 * process dies, Inngest resumes from the last finished step instead of
 * re-running the AI decision.
 */
export const routeTicket = inngest.createFunction(
  { id: "route-ticket", name: "Route a support ticket to a branch" },
  { event: ROUTE_TICKET_EVENT },
  async ({ event, step }) => {
    const message = (event.data as TicketNewEvent["data"]).message;

    const intent = await step.run("detect-intent", async () => classifyMessage(message));

    const branch = await step.run(
      "expand-branch",
      async () => branchSteps(intent.category).map((s) => ({ label: s.label, detail: s.detail })),
    );

    const executed: string[] = [];
    for (const action of branch) {
      const outcome = await step.run(
        `execute:${action.label}`,
        async () => ({ step: action.label, ok: true }),
      );
      executed.push(outcome.step);
    }

    return { message, intent, executed };
  },
);
