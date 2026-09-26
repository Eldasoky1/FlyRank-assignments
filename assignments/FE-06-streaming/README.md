# FE-06 — Streaming AI interface (capstone central interaction)

Built as the core of the capstone app (`frontend-capstone`).

## What was done
- **Streaming fetch**: `src/hooks/useStreamingChat.js` consumes the SSE-style `/api/chat` stream
  with `response.body.getReader()` + `TextDecoder`, appending tokens to `parts.stream`.
- **Streaming renderer**: `src/components/MessageList.jsx` renders the accumulating stream in a
  live region (`role="log"`, `aria-live="polite"`).
- **Markdown-safety**: text is buffered whole-part — half-finished markdown (unclosed code fences,
  dangling asterisks) never renders mid-stream because we render plain accumulated text and keep
  the buffer intact; a per-part renderer can be swapped in without breaking the stream.
- **Skeleton before first chunk** matching the bubble layout (avoids CLS).

## Deliverable check
| Criterion | Where |
| --- | --- |
| Streaming interface for central AI interaction | `useStreamingChat.js` + `MessageList.jsx` |
| No naive raw-markdown mid-stream rendering | buffered plain-text stream (see README "Streaming model") |

## Repo links
- Hook: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/hooks/useStreamingChat.js`
- Streaming renderer: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/components/MessageList.jsx`