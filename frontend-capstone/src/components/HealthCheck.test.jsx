import { render, screen } from '@testing-library/react'
import HealthCheck from './HealthCheck.jsx'

describe('HealthCheck', () => {
  it('shows loading before the fetch resolves', () => {
    global.fetch = vi.fn(() => new Promise(() => {}))
    render(<HealthCheck />)
    expect(screen.getByText(/Checking/)).toBeInTheDocument()
  })

  it('renders the ok state from fetched data', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    })
    render(<HealthCheck />)
    expect(await screen.findByTestId('health-ok')).toBeInTheDocument()
  })

  it('renders the error state when the endpoint is unreachable', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('down'))
    render(<HealthCheck />)
    expect(await screen.findByTestId('health-err')).toBeInTheDocument()
  })
})