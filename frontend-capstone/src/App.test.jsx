import { render, screen } from '@testing-library/react'
import App from './App.jsx'

describe('App layout + health tab', () => {
  it('renders the header and chat surface by default', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /StreamChat/ })).toBeInTheDocument()
    expect(screen.getByLabelText('Message the assistant')).toBeInTheDocument()
  })
})