import { useEffect, useState } from 'react'

export default function HealthCheck() {
  const [state, setState] = useState({ status: 'loading' })

  useEffect(() => {
    let alive = true
    fetch('/api/health')
      .then(async (r) => {
        const body = await r.json()
        if (alive) setState({ status: r.ok ? 'ok' : 'error', body })
      })
      .catch(() => alive && setState({ status: 'error' }))
    return () => { alive = false }
  }, [])

  return (
    <section aria-label="Health check" className="health-panel rounded-3xl border border-ink/10 bg-paper-elev p-5 sm:p-7">
      <p className="eyebrow">System status</p>
      <h2 className="display-title mt-2 text-3xl font-semibold">Health check</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-ink-mute">A small, honest signal from the local API that powers streaming and tool actions.</p>
      {state.status === 'loading' && <p className="mt-2 text-sm text-ink-mute">Checking…</p>}
      {state.status === 'ok' && (
        <p className="mt-6 rounded-2xl border border-ok/25 bg-ok-soft px-4 py-3 text-sm text-ok" data-testid="health-ok">
          All systems operational — {JSON.stringify(state.body)}
        </p>
      )}
      {state.status === 'error' && (
        <p className="mt-6 rounded-2xl border border-danger/25 bg-danger-soft px-4 py-3 text-sm text-danger" role="alert" data-testid="health-err">
          Health endpoint unreachable. Is the mock API running on :5199/api?
        </p>
      )}
    </section>
  )
}