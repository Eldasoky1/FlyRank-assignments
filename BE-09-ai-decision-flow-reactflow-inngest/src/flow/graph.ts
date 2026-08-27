import type { Edge, Node } from "@xyflow/react";
import { BRANCHES } from "../domain/branchRouter";
import type { Category, FlowStep } from "../domain/types";

export const NODE_IDS = {
  start: "start",
  intent: "intent",
  end: "end",
} as const;

export function branchNodeId(category: Category): string {
  return `branch:${category}`;
}

export interface RunState {
  intent?: Category;
  running: boolean;
  steps: FlowStep[];
}

/** Build the full decision-flow graph as React Flow nodes + edges. */
export function buildGraph(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const COL_X = 260;
  const ROW_H = 96;

  nodes.push(
    {
      id: NODE_IDS.start,
      type: "start",
      position: { x: 0, y: 220 },
      data: {},
    },
    {
      id: NODE_IDS.intent,
      type: "intent",
      position: { x: COL_X, y: 220 },
      data: {},
    },
  );

  const branchY = -220;
  BRANCHES.forEach((b, i) => {
    const id = branchNodeId(b.category);
    nodes.push({
      id,
      type: "branch",
      position: { x: COL_X * 2, y: branchY + i * ROW_H * 2 },
      data: { category: b.category, steps: b.steps },
    });
    edges.push({
      id: `e:${NODE_IDS.intent}-${id}`,
      source: NODE_IDS.intent,
      target: id,
      animated: false,
      label: b.category,
    });
  });

  nodes.push({
    id: NODE_IDS.end,
    type: "end",
    position: { x: COL_X * 3, y: 220 },
    data: {},
  });

  BRANCHES.forEach((b) => {
    edges.push({
      id: `e:${branchNodeId(b.category)}-${NODE_IDS.end}`,
      source: branchNodeId(b.category),
      target: NODE_IDS.end,
      animated: false,
    });
  });

  edges.push({
    id: `e:${NODE_IDS.start}-${NODE_IDS.intent}`,
    source: NODE_IDS.start,
    target: NODE_IDS.intent,
    animated: false,
    label: "AI decides",
  });

  return { nodes, edges };
}

export function applyRunState(nodes: Node[], edges: Edge[], state: RunState): { nodes: Node[]; edges: Edge[] } {
  const chosenBranch = state.intent ? branchNodeId(state.intent) : null;

  const styledEdges = edges.map((e) => {
    const onPath =
      chosenBranch != null && (e.target === chosenBranch || e.source === chosenBranch || e.id === `e:${NODE_IDS.start}-${NODE_IDS.intent}`);
    return {
      ...e,
      animated: onPath && state.running,
      style: onPath ? { stroke: "#7c3aed", strokeWidth: 3 } : { stroke: "#cbd5e1" },
    };
  });

  const styledNodes = nodes.map((n) => {
    if (n.id === NODE_IDS.start) return { ...n, data: { ...n.data, active: state.running || state.intent != null } };
    if (n.id === NODE_IDS.intent) return { ...n, data: { ...n.data, active: state.running || state.intent != null } };
    if (n.id === chosenBranch) return { ...n, data: { ...n.data, active: true, selected: true } };
    if (n.id === NODE_IDS.end) return { ...n, data: { ...n.data, active: state.intent != null } };
    return { ...n, data: { ...n.data, active: false } };
  });

  return { nodes: styledNodes, edges: styledEdges };
}
