export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  return (
    <div
      className={
        isUser
          ? 'message-bubble user-message self-end max-w-[85%] rounded-2xl rounded-br-sm bg-accent px-4 py-3 text-sm text-accent-fg'
          : 'message-bubble assistant-message self-start max-w-[85%] rounded-2xl rounded-bl-sm border border-ink/10 bg-paper px-4 py-3'
      }
      data-testid={isUser ? 'bubble-user' : 'bubble-assistant'}
    >
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] opacity-60">{isUser ? 'You' : 'StreamChat'}</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>
    </div>
  )
}