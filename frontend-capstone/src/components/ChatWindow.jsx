import { useState } from 'react'
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
    <section aria-label="AI chat" className="flex flex-col gap-4">
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
          className="flex items-center justify-between gap-3 rounded-control border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger"
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