export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  return (
    <div
      className={
        isUser
          ? 'self-end max-w-[85%] rounded-2xl rounded-br-sm bg-accent px-3 py-2 text-sm text-accent-fg'
          : 'self-start max-w-[85%] rounded-2xl rounded-bl-sm border border-ink/10 bg-paper-elev px-3 py-2'
      }
      data-testid={isUser ? 'bubble-user' : 'bubble-assistant'}
    >
      <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>
    </div>
  )
}