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
    <section aria-label="Health check" className="rounded-control border border-ink/10 bg-paper-elev p-4">
      <h2 className="text-base font-semibold">Health check</h2>
      {state.status === 'loading' && <p className="mt-2 text-sm text-ink-mute">Checking…</p>}
      {state.status === 'ok' && (
        <p className="mt-2 text-sm text-ok" data-testid="health-ok">
          All systems operational — {JSON.stringify(state.body)}
        </p>
      )}
      {state.status === 'error' && (
        <p className="mt-2 text-sm text-danger" role="alert" data-testid="health-err">
          Health endpoint unreachable. Is the mock API running on :5199/api?
        </p>
      )}
    </section>
  )
}