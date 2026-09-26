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
      <div className="rounded-control border border-ink/10 bg-paper-elev px-4 py-10 text-center">
        <p className="font-medium">No conversations yet — try asking about the capstone plan</p>
        <p className="mt-1 text-sm text-ink-mute">
          The assistant streams its answer in real time and can confirm before running a tool.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3" role="log" aria-live="polite">
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