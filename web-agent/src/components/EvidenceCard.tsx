import { Bug, ChevronDown, CircleCheck, Lock, Radar, Server, ShieldCheck, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import type { AuditEvidence } from '../types/audit'

type EvidenceCardProps = {
  evidence: AuditEvidence
}

const icons = {
  lock: Lock,
  shield: ShieldCheck,
  radar: Radar,
  server: Server,
  bug: Bug,
  check: CircleCheck,
  alert: TriangleAlert,
}

export default function EvidenceCard({ evidence }: EvidenceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const Icon = icons[evidence.icon ?? 'alert'] ?? TriangleAlert
  const positive = evidence.status === 'positive'

  return (
    <article className="evidence-row-expanded">
      <button
        aria-expanded={expanded}
        className="evidence-row evidence-row-button"
        onClick={() => setExpanded((current) => !current)}
        type="button"
      >
        <div className={positive ? 'evidence-icon evidence-icon-positive' : 'evidence-icon evidence-icon-warning'}>
          <Icon size={15} />
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="truncate text-sm font-medium text-neutral-100">{evidence.title}</p>
          <p className="truncate text-xs text-neutral-500">{evidence.description}</p>
        </div>
        <span className="hidden text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-500 min-[360px]:inline">
          {evidence.status}
        </span>
        <ChevronDown
          className={expanded ? 'details-chevron details-chevron-open' : 'details-chevron'}
          size={15}
        />
      </button>

      {expanded ? (
        <div className="evidence-expanded-body">
          <p className="text-sm font-medium leading-5 text-neutral-100">{evidence.title}</p>
          <p className="mt-1 text-xs leading-5 text-neutral-400">{evidence.description}</p>
          <p className="mt-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-500">
            {evidence.status}
          </p>
        </div>
      ) : null}
    </article>
  )
}
