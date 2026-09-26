import { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import HealthCheck from './components/HealthCheck.jsx'
import { useStreamingChat } from './hooks/useStreamingChat.js'

export default function App() {
  const chat = useStreamingChat()
  const [tab, setTab] = useState('chat')

  return (
    <div className="min-h-full bg-paper text-ink">
      <header className="border-b border-ink/10 bg-paper-elev px-4 py-3">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span
              className="inline-flex h-9 w-9 items-center justify-center rounded-control bg-accent text-accent-fg font-bold"
              aria-hidden="true"
            >
              ✦
            </span>
            <div>
              <h1 className="text-lg font-semibold leading-tight">StreamChat</h1>
              <p className="text-xs text-ink-mute">
                Capstone AI chat — streaming, tool states, resilient UI
              </p>
            </div>
          </div>
          <nav aria-label="Tabs" className="flex gap-1">
            {[
              ['chat', 'Chat'],
              ['health', 'Health check'],
            ].map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                aria-selected={tab === id}
                className="rounded-chip px-3 py-1.5 text-sm font-medium transition-colors data-[selected=true]:bg-accent data-[selected=true]:text-accent-fg"
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6">
        {tab === 'chat' ? <ChatWindow chat={chat} /> : <HealthCheck />}
      </main>
    </div>
  )
}