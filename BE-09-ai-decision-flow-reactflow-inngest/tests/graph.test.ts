import { describe, expect, it } from "vitest";
import { buildGraph, applyRunState, branchNodeId, type RunState } from "../src/flow/graph";
import type { Category } from "../src/domain/types";

describe("React Flow graph", () => {
  it("builds the expected node set (start, intent, 5 branches, end)", () => {
    const { nodes, edges } = buildGraph();
    expect(nodes.length).toBe(8);
    const ids = nodes.map((n) => n.id);
    expect(ids).toContain("start");
    expect(ids).toContain("intent");
    expect(ids).toContain("end");
    for (const c of ["billing", "technical", "account", "sales", "other"] as Category[]) {
      expect(ids).toContain(branchNodeId(c));
    }
    // one start->intent, one intent->branch per branch, one branch->end per branch
    expect(edges.length).toBe(1 + 5 + 5);
  });

  it("keeps branch steps when a run state is applied (regression: data.map crash)", () => {
    const { nodes, edges } = buildGraph();
    const state: RunState = { intent: "billing" as Category, running: false, steps: [] };
    const { nodes: styled } = applyRunState(nodes, edges, state);

    const billing = styled.find((n) => n.id === branchNodeId("billing"));
    expect(billing).toBeDefined();
    // the data must still carry the steps array (this was the crash source)
    const steps = (billing!.data as { steps: unknown[] }).steps;
    expect(Array.isArray(steps)).toBe(true);
    expect(steps.length).toBeGreaterThan(0);
    expect((billing!.data as { selected?: boolean }).selected).toBe(true);
    expect((billing!.data as { active?: boolean }).active).toBe(true);
  });

  it("marks the winning branch edge and leaves others dimmed", () => {
    const { nodes, edges } = buildGraph();
    const state: RunState = { intent: "sales", running: true, steps: [] };
    const { edges: styled } = applyRunState(nodes, edges, state);

    const winner = styled.find((e) => e.target === branchNodeId("sales"));
    const loser = styled.find((e) => e.target === branchNodeId("technical"));
    expect(winner!.animated).toBe(true);
    expect(loser!.animated).toBe(false);
  });
});
