import { render, screen } from '@testing-library/react'
import MessageList from './MessageList.jsx'

const emptyParts = { stream: '', activeTool: null }

describe('MessageList', () => {
  it('advertises a designed empty state, not an apology', () => {
    render(<MessageList messages={[]} parts={emptyParts} isStreaming={false} />)
    expect(screen.getByText(/No conversations yet/)).toBeInTheDocument()
    expect(screen.getByText(/try asking about the capstone plan/)).toBeInTheDocument()
  })

  it('renders user and assistant bubbles with distinct roles', () => {
    const messages = [
      { id: 1, role: 'user', text: 'hello' },
      { id: 2, role: 'assistant', text: 'hi there' },
    ]
    render(<MessageList messages={messages} parts={emptyParts} isStreaming={false} />)
    expect(screen.getByTestId('bubble-user')).toHaveTextContent('hello')
    expect(screen.getByTestId('bubble-assistant')).toHaveTextContent('hi there')
  })

  it('renders streaming text as it arrives', () => {
    render(<MessageList messages={[]} parts={{ stream: 'streaming snippet', activeTool: null }} isStreaming />)
    expect(screen.getByText('streaming snippet')).toBeInTheDocument()
  })

  it('shows a skeleton while the first chunk is pending', () => {
    render(
      <MessageList
        messages={[{ id: 1, role: 'user', text: 'hello' }]}
        parts={emptyParts}
        isStreaming
      />,
    )
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })
})