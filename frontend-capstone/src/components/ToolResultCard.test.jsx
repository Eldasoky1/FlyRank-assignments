import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ToolResultCard from './ToolResultCard.jsx'

const base = { name: 'check_dates', input: 'now' }

describe('ToolResultCard states', () => {
  it('renders the running state with role status', () => {
    render(<ToolResultCard activeTool={{ ...base, state: 'running', output: null, error: null }} />)
    expect(screen.getByRole('status')).toHaveAttribute('data-tool-state', 'running')
  })

  it('renders the needs_input state with confirm and cancel buttons', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    render(
      <ToolResultCard
        activeTool={{ ...base, state: 'needs_input', output: null, error: null }}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Confirm & run' }))
    expect(onConfirm).toHaveBeenCalled()
  })

  it('renders a designed error state, not a crash', () => {
    render(
      <ToolResultCard
        activeTool={{ ...base, state: 'error', output: null, error: 'Connection lost (simulated)' }}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )
    expect(screen.getByTestId('tool-error')).toHaveTextContent('Connection lost (simulated)')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('renders the result output', () => {
    render(
      <ToolResultCard
        activeTool={{ ...base, state: 'result', output: '{"slots":[]}', error: null }}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )
    expect(screen.getByTestId('tool-result')).toHaveTextContent('{"slots":[]}')
  })
})