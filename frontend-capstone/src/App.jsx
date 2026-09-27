import { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import HealthCheck from './components/HealthCheck.jsx'
import { useStreamingChat } from './hooks/useStreamingChat.js'

export default function App() {
  const chat = useStreamingChat()
  const [tab, setTab] = useState('chat')

  return (
    <div className="app-shell min-h-full bg-paper text-ink">
      <header className="app-header px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-5">
          <div className="flex items-center gap-3">
            <span
              className="brand-mark inline-flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-fg font-bold"
              aria-hidden="true"
            >
              SC
            </span>
            <div>
              <p className="eyebrow">Frontend AI capstone</p>
              <h1 className="display-title text-xl font-semibold leading-tight">StreamChat</h1>
            </div>
          </div>
          <nav aria-label="Workspace views" className="tab-nav flex gap-1 rounded-full p-1">
            {[
              ['chat', 'Chat'],
              ['health', 'Health check'],
            ].map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                aria-selected={tab === id}
                data-selected={tab === id}
                className="tab-button rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_250px] lg:py-10">
        {tab === 'chat' ? <ChatWindow chat={chat} /> : <HealthCheck />}
        {tab === 'chat' && (
          <aside className="workspace-note hidden self-start rounded-2xl border border-ink/10 bg-paper-elev p-5 lg:block">
            <p className="eyebrow">Workspace notes</p>
            <h2 className="mt-2 font-display text-2xl leading-tight">Think in public.</h2>
            <p className="mt-3 text-sm leading-6 text-ink-mute">
              StreamChat keeps the useful parts visible: the response, the action it wants to take, and what happened next.
            </p>
            <div className="mt-6 border-t border-ink/10 pt-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-mute">Available now</p>
              <ul className="mt-3 space-y-3 text-sm">
                <li className="flex gap-2"><span className="status-dot bg-ok" />Streaming answers</li>
                <li className="flex gap-2"><span className="status-dot bg-accent" />Tool confirmation</li>
                <li className="flex gap-2"><span className="status-dot bg-ink-mute" />Resilient retries</li>
              </ul>
            </div>
          </aside>
        )}
      </main>
    </div>
  )
}