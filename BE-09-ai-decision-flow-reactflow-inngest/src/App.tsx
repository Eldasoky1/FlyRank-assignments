import { useMemo, useState } from "react";
import { FlowCanvas } from "./components/FlowCanvas";
import { buildGraph, applyRunState, type RunState } from "./flow/graph";
import { runDecisionFlow } from "./flow/runFlow";

const DEFAULT_MESSAGE =
  "I was charged twice for the same plan and I would like a refund please.";

export default function App() {
  const base = useMemo(() => buildGraph(), []);
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const [state, setState] = useState<RunState>({ running: false, steps: [] });
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);

  const view = useMemo(
    () => applyRunState(base.nodes, base.edges, state),
    [base, state],
  );

  async function run() {
    if (!message.trim()) return;
    setError(null);
    setLog([]);
    setState({ running: true, steps: [] });

    try {
      const result = await runDecisionFlow(message, {
        onIntent: (intent) => setState({ running: true, intent: intent.category, steps: [] }),
        onStep: (step, all) => {
          setLog((l) => [...l, `• ${step.status === "done" ? "✔ " : "› "}${step.label}`]);
          setState((s) => ({ ...s, steps: [...all] }));
        },
        delayMs: 300,
      });

      setState({ running: false, intent: result.intent.category, steps: result.steps });
    } catch (e) {
      setState({ running: false, steps: [] });
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>AI Decision Flow</h1>
        <span className="badge">React Flow + Inngest</span>
      </header>

      <div className="layout">
        <aside className="panel">
          <label>Support message</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
            data-testid="message-input"
          />
          <button onClick={run} disabled={state.running} data-testid="run-button">
            {state.running ? "Running…" : "Run decision flow"}
          </button>

          {error && <p className="error">{error}</p>}

          <h3>Result</h3>
          <p data-testid="result-intent">
            {state.intent ? (
              <>
                Routed to <strong>{state.intent}</strong>
              </>
            ) : (
              "Not run yet"
            )}
          </p>

          <h3>Run log</h3>
          <ul className="log" data-testid="run-log">
            {log.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </aside>

        <main className="canvas">
          <FlowCanvas nodes={view.nodes} edges={view.edges} />
        </main>
      </div>

      <footer className="note">
        The visible flow is driven by the same step sequence as the Inngest{" "}
        <code>routeTicket</code> function (<code>inngest/routeTicket.ts</code>).
      </footer>
    </div>
  );
}
