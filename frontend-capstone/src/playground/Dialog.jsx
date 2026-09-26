import { useCallback, useEffect, useRef, useState } from 'react'

// Dialog with focus trap + return of focus, per W3C ARIA APG Dialog (Modal) pattern.
export default function Dialog({ label, triggerLabel = 'Open dialog', children, onClose }) {
  const [open, setOpen] = useState(false)
  const dialogRef = useRef(null)
  const triggerRef = useRef(null)

  const close = useCallback(() => {
    setOpen(false)
    onClose?.()
    requestAnimationFrame(() => triggerRef.current?.focus())
  }, [onClose])

  useEffect(() => {
    if (!open) return
    const el = dialogRef.current
    el?.focus()
    const onKey = (e) => {
      if (e.key === 'Escape') close()
      if (e.key === 'Tab') {
        const focusables = el.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        )
        if (!focusables.length) return
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, close])

  return (
    <div>
      <button type="button" ref={triggerRef} onClick={() => setOpen(true)}>
        {triggerLabel}
      </button>
      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4">
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={label}
            tabIndex={-1}
            className="w-full max-w-sm rounded-control border border-ink/10 bg-paper-elev p-4 shadow-lg outline-none"
          >
            <h2 className="text-base font-semibold">{label}</h2>
            <div className="mt-2">{children}</div>
            <button
              type="button"
              onClick={close}
              className="mt-4 rounded-chip border border-ink/20 px-3 py-1 text-sm"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}