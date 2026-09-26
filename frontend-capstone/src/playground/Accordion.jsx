import { useId, useState } from 'react'

// Accordion with three sections, per W3C ARIA APG Accordion pattern (buttons + regions).
export default function Accordion({ panels }) {
  const baseId = useId()
  const [openIdx, setOpenIdx] = useState(0)

  return (
    <div className="divide-y divide-ink/10 rounded-control border border-ink/10 bg-paper-elev">
      {panels.map((p, i) => {
        const isOpen = openIdx === i
        const headId = `${baseId}-head-${i}`
        const panelId = `${baseId}-panel-${i}`
        return (
          <div key={i}>
            <h3 className="m-0">
              <button
                type="button"
                id={headId}
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => setOpenIdx(isOpen ? -1 : i)}
                className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left text-sm font-medium"
              >
                {p.title}
                <span aria-hidden="true" className="text-ink-mute transition-transform">
                  {isOpen ? '−' : '+'}
                </span>
              </button>
            </h3>
            <div
              id={panelId}
              role="region"
              aria-labelledby={headId}
              hidden={!isOpen}
              className="px-4 pb-3 text-sm text-ink-mute"
            >
              {p.body}
            </div>
          </div>
        )
      })}
    </div>
  )
}