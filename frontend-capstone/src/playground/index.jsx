import Accordion from './Accordion.jsx'
import Combobox from './Combobox.jsx'
import Dialog from './Dialog.jsx'

const CITIES = ['Cairo', 'Alexandria', 'Giza', 'Sharm El Sheikh', 'Luxor', 'Aswan', 'Hurghada']

export default function AccessiblePlayground() {
  return (
    <section className="flex flex-col gap-8">
      <Accordion
        panels={[
          { title: 'Why accessible components?', body: 'Keyboard + screen-reader parity is the baseline for a production UI.' },
          { title: 'What changed vs shadcn', body: 'See NOTES.md — gaps like missing arrow-key listbox nav and Escape-in-accordion are called out.' },
          { title: 'What I would add next', body: 'Reduced-motion handling for tool transitions and a focus-visible ring system.' },
        ]}
      />
      <Combobox options={CITIES} label="Filter by city" />
      <Dialog label="Delete project" triggerLabel="Open modal dialog">
        <p className="text-sm text-ink-mute">This is a focus-trapped, Escape-closable modal.</p>
      </Dialog>
    </section>
  )
}