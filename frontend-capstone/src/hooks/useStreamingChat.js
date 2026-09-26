import { useCallback, useRef, useState } from 'react'

const SABOTAGES = ['net-down', 'mid-stream', 'http-429', 'bad-json']

function nextSabotage() {
  const list = window.__SABOTAGE ?? []
  return list.length ? list[0] : null
}

let idCounter = 0

export function useStreamingChat() {
  const [messages, setMessages] = useState([])
  const [parts, setParts] = useState({ stream: '', activeTool: null })
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  const finish = useCallback((text) => {
    setMessages((m) => [...m, { id: ++idCounter, role: 'assistant', text }])
    setParts({ stream: '', activeTool: null })
    setIsStreaming(false)
    setStatus('idle')
  }, [])

  const streamAnswer = useCallback(
    async (question) => {
      const sab = nextSabotage()
      setIsStreaming(true)
      setStatus('streaming')
      setParts({ stream: '', activeTool: null })
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: question, sabotage: sab }),
        })
        if (!res.ok) {
          if (res.status === 429) throw new Error('Rate limited (429). Wait a moment and retry.')
          throw new Error(`Request failed with ${res.status}`)
        }
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let acc = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          acc += decoder.decode(value, { stream: true })
          if (sab === 'mid-stream' && acc.length > 12) {
            throw new Error('Connection lost mid-stream (simulated).')
          }
          if (sab === 'bad-json' && acc.length > 24) {
            throw new Error('Malformed tool JSON (simulated).')
          }
          setParts((p) => ({ ...p, stream: acc }))
        }
        if (sab === 'empty') throw new Error('Empty response (simulated).')
        finish(acc)
      } catch (e) {
        setError(e.message || String(e))
        setStatus('error')
        setIsStreaming(false)
      }
    },
    [finish],
  )
  const streamAnswerRef = useRef(streamAnswer)
  streamAnswerRef.current = streamAnswer

  const send = useCallback(
    async (userText) => {
      setError(null)
      const toolIntent = /tool|check|schedule|dates|run/.test(userText)
      setMessages((m) => [...m, { id: ++idCounter, role: 'user', text: userText }])
      if (toolIntent) {
        setStatus('tool-waiting')
        setParts({
          stream: '',
          activeTool: { name: 'check_dates', state: 'needs_input', input: userText, output: null, error: null },
        })
        return
      }
      await streamAnswerRef.current(userText)
    },
    [],
  )

  const runTool = useCallback(async () => {
    setError(null)
    setStatus('tool-running')
    const sab = nextSabotage()
    setParts({
      stream: '',
      activeTool: { name: 'check_dates', state: 'running', input: 'now', output: null, error: null },
    })
    await new Promise((r) => setTimeout(r, 300))
    if (sab === 'bad-json' || sab === 'net-down') {
      setParts({
        stream: '',
        activeTool: { name: 'check_dates', state: 'error', input: 'now', output: null, error: 'Could not reach the schedule service (simulated failure).' },
      })
      setStatus('error')
      setIsStreaming(false)
      return
    }
    const output = JSON.stringify({ slots: ['2026-10-01', '2026-10-02'], tz: 'UTC' })
    setParts({ stream: '', activeTool: { name: 'check_dates', state: 'result', input: 'now', output, error: null } })
    setStatus('tool-result')
    setIsStreaming(false)
  }, [])

  const confirmTool = useCallback(() => runTool(), [runTool])

  const cancelTool = useCallback(() => {
    setParts({ stream: '', activeTool: null })
    setStatus('idle')
    setIsStreaming(false)
  }, [])

  const retryLast = useCallback(async () => {
    setError(null)
    const last = messagesRef.current[messagesRef.current.length - 1]
    if (last?.role === 'user' && last.text) {
      await send(last.text)
    } else if (parts.activeTool?.state === 'error') {
      await runTool()
    } else {
      await streamAnswerRef.current('Summarise the capstone plan.')
    }
  }, [parts.activeTool, runTool, send])

  return {
    messages,
    parts,
    status,
    error,
    isStreaming,
    send,
    retryLast,
    runTool,
    confirmTool,
    cancelTool,
  }
}