import ChatComposer from './ChatComposer.jsx'
import MessageList from './MessageList.jsx'
import ToolResultCard from './ToolResultCard.jsx'

export default function ChatWindow({ chat }) {
  const {
    messages,
    parts,
    status,
    error,
    isStreaming,
    send,
    retryLast,
    runTool,
    confirmTool,
    cancelTool,
  } = chat

  return (
    <section aria-label="AI chat" className="chat-workspace flex flex-col gap-4">
      <div className="flex items-end justify-between gap-4 px-1">
        <div>
          <p className="eyebrow">Conversation</p>
          <h2 className="display-title mt-1 text-3xl font-semibold sm:text-4xl">A calm place to think.</h2>
        </div>
        <span className="live-pill hidden items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium sm:inline-flex">
          <span className="status-dot bg-ok" /> Ready
        </span>
      </div>
      <MessageList messages={messages} parts={parts} isStreaming={isStreaming} />

      {status === 'tool-waiting' && (
        <ToolResultCard
          activeTool={parts.activeTool}
          onConfirm={confirmTool}
          onCancel={cancelTool}
        />
      )}

      {error && (
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-2xl border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={retryLast}
            className="rounded-chip border border-danger/30 bg-paper-elev px-2.5 py-1 font-medium"
          >
            Retry
          </button>
        </div>
      )}

      <ChatComposer
        onSend={send}
        onRunTool={runTool}
        isBusy={isStreaming || status === 'tool-waiting'}
      />
    </section>
  )
}