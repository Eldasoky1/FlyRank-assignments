export default function ToolResultCard({ activeTool, onConfirm, onCancel }) {
  if (!activeTool) return null
  const { name, state, input, output, error } = activeTool

  return (
    <div
      role="status"
      data-tool-state={state}
      className="rounded-control border border-accent/30 bg-accent-soft p-3"
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium">
          <span aria-hidden="true">🔧</span> {name}
        </p>
        <span className="rounded-chip bg-paper-elev px-2 py-0.5 text-xs font-mono uppercase">
          {state}
        </span>
      </div>

      {state === 'running' && (
        <p className="mt-1 text-sm text-ink-mute">Running with input: “{input}”…</p>
      )}

      {state === 'needs_input' && (
        <div className="mt-2 flex flex-col gap-2">
          <p className="text-sm text-ink-mute">
            The model wants to run <code className="font-mono">{name}</code> with input “{input}”.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onConfirm}
              className="rounded-chip bg-accent px-3 py-1 text-xs font-medium text-accent-fg"
            >
              Confirm & run
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="rounded-chip border border-ink/20 bg-paper-elev px-3 py-1 text-xs font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {state === 'result' && (
        <p className="mt-1 text-sm" data-testid="tool-result">
          Output: <code className="font-mono">{output}</code>
        </p>
      )}

      {state === 'error' && (
        <div className="mt-2 flex flex-col gap-2 rounded-control border border-danger/30 bg-danger-soft p-2">
          <p className="text-sm text-danger" data-testid="tool-error">
            {(error || 'Tool execution failed').toString()}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onConfirm}
              className="self-start rounded-chip bg-accent px-3 py-1 text-xs font-medium text-accent-fg"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="self-start rounded-chip border border-ink/20 bg-paper-elev px-3 py-1 text-xs font-medium"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  )
}