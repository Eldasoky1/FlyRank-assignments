import { useCallback } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  Handle,
  Position,
  type Node,
  type NodeProps,
  type Edge,
  type NodeTypes,
  type OnInit,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Category, FlowStep } from "../domain/types";

const BOX: React.CSSProperties = { borderRadius: 10, padding: "8px 14px", color: "#fff", fontSize: 13 };

function StartNode({ data }: NodeProps) {
  return (
    <div style={{ ...BOX, background: data.active ? "#10b981" : "#94a3b8" }} data-testid="node-start">
      <Handle type="source" position={Position.Right} />
      <strong>Ticket received</strong>
    </div>
  );
}

function IntentNode({ data }: NodeProps) {
  return (
    <div style={{ ...BOX, background: data.active ? "#7c3aed" : "#94a3b8" }} data-testid="node-intent">
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
      <strong>AI · detect intent</strong>
    </div>
  );
}

function BranchNode({ data }: NodeProps) {
  const { category, steps, active, selected } = data as {
    category: Category;
    steps: Omit<FlowStep, "status" | "id">[];
    active: boolean;
    selected?: boolean;
  };
  return (
    <div
      data-testid={`node-branch-${category}`}
      style={{
        ...BOX,
        width: 210,
        background: active ? "#0ea5e9" : "#94a3b8",
        outline: selected ? "3px solid #0f172a" : "none",
      }}
    >
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
      <strong style={{ textTransform: "capitalize" }}>{category}</strong>
      <ul style={{ margin: "6px 0 0 0", paddingLeft: 16, fontSize: 11 }}>
        {steps.map((s) => (
          <li key={s.label}>{s.label}</li>
        ))}
      </ul>
    </div>
  );
}

function EndNode({ data }: NodeProps) {
  return (
    <div style={{ ...BOX, background: data.active ? "#f59e0b" : "#94a3b8" }} data-testid="node-end">
      <Handle type="target" position={Position.Left} />
      <strong>Resolved</strong>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  start: StartNode,
  intent: IntentNode,
  branch: BranchNode,
  end: EndNode,
};

interface FlowCanvasProps {
  nodes: Node[];
  edges: Edge[];
}

function Canvas({ nodes, edges }: FlowCanvasProps) {
  const onInit = useCallback<OnInit>((instance) => {
    requestAnimationFrame(() => instance.fitView({ padding: 0.3 }));
  }, []);

  return (
    <div style={{ height: "100%", width: "100%" }} data-testid="flow-canvas">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView proOptions={{ hideAttribution: true }} onInit={onInit}>
        <Background gap={18} />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export function FlowCanvas({ nodes, edges }: FlowCanvasProps) {
  return (
    <ReactFlowProvider>
      <Canvas nodes={nodes} edges={edges} />
    </ReactFlowProvider>
  );
}
