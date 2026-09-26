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
    <form onSubmit={submit} aria-label="Compose message" className="flex flex-col gap-2">
      <label htmlFor="composer" className="sr-only">
        Message the assistant
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="composer"
          rows={2}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask the assistant…"
          className="flex-1 resize-none rounded-control border border-ink/20 bg-paper-elev px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={isBusy || !value.trim()}
          className="rounded-control bg-accent px-4 py-2 text-sm font-medium text-accent-fg transition-opacity disabled:opacity-50"
        >
          Send
        </button>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onRunTool}
          disabled={isBusy}
          className="self-start rounded-chip border border-ink/20 bg-paper-elev px-3 py-1 text-xs font-medium disabled:opacity-50"
        >
          Run “check dates” tool
        </button>
        <span className="text-xs text-ink-mute">
          The model asks before a tool runs; every failure is designed, not a crash.
        </span>
      </div>
    </form>
  )
}