// Dev-mode mock backend that streams the assistant reply word-by-word (SSE) and
// serves /api/health. Run separately during development; not shipped to prod.
import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'

const WORD = (i) => `token-${i}`

const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost')

  if (url.pathname === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ status: 'ok', service: 'frontend-capstone-mock', ts: Date.now() }))
    return
  }

  if (url.pathname === '/api/chat') {
    let body = ''
    req.on('data', (c) => (body += c))
    req.on('end', () => {
      let sabotage = null
      try { sabotage = JSON.parse(body).sabotage ?? null } catch {}
      const sentence = `Here is the assistant's streamed reply about your message. It ships in short chunks so the UI can render typing, then buffers markdown so nothing breaks mid-stream.`

      if (sabotage === 'http-429') {
        res.writeHead(429, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'rate limited' }))
        return
      }
      if (sabotage === 'net-down' || sabotage === 'mid-stream') {
        res.writeHead(200, { 'Content-Type': 'text/event-stream' })
        res.write('data: ' + WORD(0) + '\n\n')
        setTimeout(() => res.destroy(), 40)
        return
      }
      if (sabotage === 'bad-json') {
        res.writeHead(200, { 'Content-Type': 'text/event-stream' })
        const bad = 'data: {"broken": '
        res.write(bad)
        setTimeout(() => res.end(), 40)
        return
      }
      if (sabotage === 'empty') {
        res.writeHead(200, { 'Content-Type': 'text/event-stream' })
        res.end()
        return
      }

      res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' })
      const words = sentence.split(' ')
      let i = 0
      const timer = setInterval(() => {
        if (i >= words.length) {
          clearInterval(timer)
          res.write('data: [DONE]\n\n')
          res.end()
          return
        }
        res.write(`data: ${words[i]} \n\n`)
        i += 1
      }, 60)
    })
    return
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' })
  res.end('not found')
})

server.listen(5199, () => console.log('mock api on http://localhost:5199'))