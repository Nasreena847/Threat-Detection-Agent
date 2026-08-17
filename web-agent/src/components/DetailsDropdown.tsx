import { ChevronDown } from 'lucide-react'
import type { AuditReport } from '../types/audit'
import EvidenceList from './EvidenceList'

type DetailsDropdownProps = {
  audit: AuditReport
  expanded: boolean
  onToggle: () => void
}

const rowsFromRecord = (record?: Record<string, unknown>) =>
  Object.entries(record ?? {}).filter(([, value]) => value !== undefined && value !== null)

export default function DetailsDropdown({ audit, expanded, onToggle }: DetailsDropdownProps) {
  return (
    <section className="glass-card overflow-hidden">
      <button
        aria-expanded={expanded}
        className="details-trigger"
        onClick={onToggle}
        type="button"
      >
        <span>
          <span className="block text-sm font-semibold text-white">Details</span>
          <span className="text-xs text-neutral-500">{audit.evidence.length} evidence signals</span>
        </span>
        <ChevronDown
          className={expanded ? 'details-chevron details-chevron-open' : 'details-chevron'}
          size={18}
        />
      </button>

      {expanded ? (
        <div className="details-panel">
          <EvidenceList evidence={audit.evidence} />
          <DetailGroup title="Risk components" values={rowsFromRecord(audit.components)} />
          <DetailGroup title="Threat intelligence" values={rowsFromRecord(audit.threatIntel)} />
          <DetailGroup title="Model" values={rowsFromRecord(audit.ml)} />
        </div>
      ) : null}
    </section>
  )
}

type DetailGroupProps = {
  title: string
  values: [string, unknown][]
}

function DetailGroup({ title, values }: DetailGroupProps) {
  if (values.length === 0) return null

  return (
    <div className="mt-3 rounded-2xl border border-white/8 bg-black/20 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-neutral-500">{title}</p>
      <div className="space-y-1.5">
        {values.map(([key, value]) => (
          <div className="flex items-start justify-between gap-3 text-xs" key={key}>
            <span className="text-neutral-500">{key}</span>
            <span className="max-w-[190px] break-words text-right text-neutral-200">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
