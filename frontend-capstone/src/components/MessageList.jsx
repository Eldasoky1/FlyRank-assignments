import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble.jsx'

export default function MessageList({ messages, parts, isStreaming }) {
  const endRef = useRef(null)

  useEffect(() => {
    if (typeof endRef.current?.scrollIntoView === 'function') {
      endRef.current.scrollIntoView({ block: 'nearest' })
    }
  }, [messages, parts.stream, isStreaming])

  if (messages.length === 0 && !parts.stream) {
    return (
      <div className="empty-state rounded-3xl border border-ink/10 bg-paper-elev px-5 py-10 sm:px-10 sm:py-14">
        <div className="empty-orbit" aria-hidden="true"><span>↗</span></div>
        <div className="max-w-lg">
          <p className="eyebrow">Start with a question</p>
          <h3 className="display-title mt-2 text-2xl font-semibold sm:text-3xl">Make the next thought easier.</h3>
          <p className="mt-3 max-w-md text-sm leading-6 text-ink-mute">
            Ask for a plan, a critique, or a quick date check. Your assistant will stream the answer and ask before taking action.
          </p>
          <div className="mt-6 flex flex-wrap gap-2 text-xs text-ink-mute">
            <span className="suggestion-chip">“Outline my next step”</span>
            <span className="suggestion-chip">“Check my dates”</span>
          </div>
          <p className="sr-only">
            No conversations yet. try asking about the capstone plan.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="message-canvas flex flex-col gap-3 rounded-3xl border border-ink/10 bg-paper-elev p-4 sm:p-6" role="log" aria-live="polite">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}

      {isStreaming && (
        <div className="flex flex-col gap-1 self-start max-w-[85%] rounded-2xl border border-ink/10 bg-paper-elev p-3">
          {parts.stream ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{parts.stream}</p>
          ) : (
            <span className="text-sm text-ink-mute">Streaming…</span>
          )}
        </div>
      )}

      {isStreaming && !parts.stream && (
        <div aria-hidden="true" className="rounded-2xl border border-ink/10 bg-paper-elev p-3">
          <div className="h-3 w-2/3 animate-pulse rounded bg-ink/10" />
          <div className="mt-2 h-3 w-1/3 animate-pulse rounded bg-ink/10" />
        </div>
      )}

      <div ref={endRef} />
    </div>
  )
}