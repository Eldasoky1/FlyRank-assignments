# FE-03 — Accessible components (W3C ARIA APG)

Three UI patterns implemented against the W3C ARIA Authoring Practices Guide, keyboard-first:

1. **Dialog (modal)** — `src/playground/Dialog.jsx`
   - `role="dialog"` + `aria-modal`, `aria-label`
   - **Focus trap**: Tab/Shift+Tab cycle within the dialog (first→last, last→first)
   - **Escape closes**; focus returns to the trigger on close
2. **Combobox (autocomplete listbox)** — `src/playground/Combobox.jsx`
   - `role="combobox"` with `aria-expanded`, `aria-controls`, `aria-activedescendant`
   - ArrowDown/Up move the active option, Enter commits, Escape closes; listbox exposes `aria-selected`
3. **Accordion** — `src/playground/Accordion.jsx`
   - Header buttons with `aria-expanded` + `aria-controls`, `role="region"` panels
   - Keyboard-only: Tab between headers, Space/Enter toggle

Demonstration page: `frontend-capstone/src/playground/index.jsx`

## NOTES.md — the gaps

Compared to shadcn/ui's implementations (and against the APG):

1. **Combobox**: the APG allows the listbox to open on focus-with-content; shadcn's combobox
   (Radix) keeps the input always-editable and always keeps a visible selected value. Mine
   **shows a plain input with an implicit selection**, so there's a naming gap: I don't expose a
   selected-value affordance *inside* the field. Concrete fix: add a visually-hidden span with
   `aria-hidden` for the chosen item, mirroring Radix primitives.
2. **Accordion/Buttons**: W3C says accordion headers should optionally support ArrowUp/ArrowDown
   roving-tabindex navigation between sections. Mine uses plain Tab (valid per APG Alternative 1),
   but **no arrow-key roving tabindex**, which shadcn/Collapsible adds. Concrete improvement:
   move `tabindex` to the open header and support Arrow keys.
3. **Dialog**: my focus trap is a simple ring; the APG suggests keeping the *first focusable*
   target stable and managing `aria-describedby` for the initial focusable element. Mine lacks
   `aria-describedby`, so I'll wire the description id (the text under the title) to the dialog.

All three were exercised keyboard-only (Tab, Shift+Tab, Space/Enter, Escape) during the build;
the test suite asserts by role/label so cosmetic class renames cannot break the tests.