import { describe, expect, it } from "vitest";
import { runDecisionFlow } from "../src/flow/runFlow";
import { routeTicket, ROUTE_TICKET_EVENT } from "../inngest/routeTicket";

describe("decision flow runner", () => {
  it("executes the branch steps in order, all ending 'done'", async () => {
    const result = await runDecisionFlow("I was charged twice, please refund", { delayMs: 0 });
    expect(result.intent.category).toBe("billing");
    expect(result.steps.every((s) => s.status === "done")).toBe(true);
    expect(result.steps.map((s) => s.label)).toEqual([
      "Look up subscription",
      "Compute refund",
      "Issue refund",
    ]);
  });

  it("fires onIntent with the resolved category before steps", async () => {
    let seen = "";
    await runDecisionFlow("reset my password", {
      onIntent: (i) => (seen = i.category),
      delayMs: 0,
    });
    expect(seen).toBe("account");
  });

  it("emits each step transition through onStep", async () => {
    const seen: string[] = [];
    await runDecisionFlow("the app crashed", {
      onStep: (s) => seen.push(`${s.label}:${s.status}`),
      delayMs: 0,
    });
    expect(seen[0]).toBe("Gather logs:running");
    expect(seen).toContain("Propose fix:done");
  });
});

describe("Inngest step function definition", () => {
  it("exports a routeTicket workflow object triggered by 'ticket/new'", () => {
    expect(routeTicket).toBeTruthy();
    expect(ROUTE_TICKET_EVENT).toBe("ticket/new");
  });
});
