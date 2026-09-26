import { useEffect, useRef, useState } from 'react'

// Simple combobox (autocomplete listbox), per W3C ARIA APG Combobox pattern (list + listbox).
export default function Combobox({ options, label = 'Pick a city' }) {
  const [value, setValue] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const boxRef = useRef(null)

  const matches = options.filter((o) => o.toLowerCase().includes(value.toLowerCase()))
  const visible = open && matches.length > 0

  useEffect(() => {
    setActive(visible && matches.length ? 0 : -1)
  }, [value, open]) // eslint-disable-line react-hooks/exhaustive-deps

  function choose(i) {
    if (i >= 0 && i < matches.length) {
      setValue(matches[i])
      setOpen(false)
    }
  }

  function onKey(e) {
    if (!visible) {
      if (e.key === 'ArrowDown') { setOpen(true); return }
      return
    }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => (a + 1) % matches.length) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => (a - 1 + matches.length) % matches.length) }
    else if (e.key === 'Enter') { e.preventDefault(); choose(active) }
    else if (e.key === 'Escape') { setOpen(false); boxRef.current?.focus() }
  }

  return (
    <div>
      <label htmlFor="combo" className="text-sm font-medium">{label}</label>
      <div className="relative mt-1">
        <input
          ref={boxRef}
          id="combo"
          role="combobox"
          aria-expanded={visible}
          aria-controls="combo-listbox"
          aria-activedescendant={active >= 0 ? `combo-opt-${active}` : undefined}
          value={value}
          onChange={(e) => { setValue(e.target.value); setOpen(true) }}
          onKeyDown={onKey}
          onFocus={() => setOpen(true)}
          autoComplete="off"
          className="w-full rounded-control border border-ink/20 px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
        {visible && (
          <ul
            id="combo-listbox"
            role="listbox"
            aria-label={`${label} options`}
            className="absolute z-40 mt-1 w-full rounded-control border border-ink/10 bg-paper-elev shadow-lg"
          >
            {matches.map((m, i) => (
              <li
                key={m}
                id={`combo-opt-${i}`}
                role="option"
                aria-selected={i === active}
                onMouseEnter={() => setActive(i)}
                onClick={() => choose(i)}
                className={`cursor-pointer px-3 py-1.5 text-sm ${i === active ? 'bg-accent-soft text-accent' : ''}`}
              >
                {m}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}