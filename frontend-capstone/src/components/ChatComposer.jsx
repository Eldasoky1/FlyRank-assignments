import { useState } from 'react'

export default function ChatComposer({ onSend, onRunTool, isBusy }) {
  const [value, setValue] = useState('')

  function submit(e) {
    e.preventDefault()
    const text = value.trim()
    if (!text || isBusy) return
    setValue('')
    onSend(text)
  }

  return (
    <form onSubmit={submit} aria-label="Compose message" className="composer-shell flex flex-col gap-3 rounded-3xl border border-ink/10 bg-paper-elev p-3 sm:p-4">
      <label htmlFor="composer" className="sr-only">
        Message the assistant
      </label>
      <div className="flex items-end gap-3">
        <textarea
          id="composer"
          rows={2}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask the assistant…"
          className="composer-input min-h-14 flex-1 resize-none rounded-2xl border border-ink/15 bg-paper px-4 py-3 text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="submit"
          disabled={isBusy || !value.trim()}
          className="send-button rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-accent-fg transition-opacity disabled:opacity-50"
        >
          Send
        </button>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={onRunTool}
          disabled={isBusy}
          className="tool-button self-start rounded-full border border-ink/15 bg-paper px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          Run “check dates” tool
        </button>
        <span className="text-xs text-ink-mute">
          Enter to send · tool runs always ask first
        </span>
      </div>
    </form>
  )
}