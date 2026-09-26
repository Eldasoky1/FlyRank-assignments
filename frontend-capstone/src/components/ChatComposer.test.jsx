import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatComposer from './ChatComposer.jsx'

describe('ChatComposer', () => {
  it('has a labelled textarea and a send button', () => {
    render(<ChatComposer onSend={vi.fn()} onRunTool={vi.fn()} isBusy={false} />)
    expect(screen.getByLabelText('Message the assistant')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
  })

  it('sends the trimmed value and clears the box', async () => {
    const user = userEvent.setup()
    const onSend = vi.fn()
    render(<ChatComposer onSend={onSend} onRunTool={vi.fn()} isBusy={false} />)
    await user.type(screen.getByLabelText('Message the assistant'), '  hello  ')
    await user.click(screen.getByRole('button', { name: 'Send' }))
    expect(onSend).toHaveBeenCalledWith('hello')
    expect(screen.getByLabelText('Message the assistant')).toHaveValue('')
  })

  it('disables send while busy', () => {
    render(<ChatComposer onSend={vi.fn()} onRunTool={vi.fn()} isBusy />)
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()
  })
})