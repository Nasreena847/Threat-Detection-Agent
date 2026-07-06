import { Bug, CircleCheck, Lock, Radar, Server, ShieldCheck, TriangleAlert } from 'lucide-react'
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
  const Icon = icons[evidence.icon ?? 'alert'] ?? TriangleAlert
  const positive = evidence.status === 'positive'

  return (
    <article className="evidence-row">
      <div className={positive ? 'evidence-icon evidence-icon-positive' : 'evidence-icon evidence-icon-warning'}>
        <Icon size={15} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-neutral-100">{evidence.title}</p>
        <p className="truncate text-xs text-neutral-500">{evidence.description}</p>
      </div>
      <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-neutral-500">
        {evidence.status}
      </span>
    </article>
  )
}
