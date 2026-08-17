import { TriangleAlert } from 'lucide-react'
import type { AuditEvidence } from '../types/audit'

type AdWarningCardProps = {
  evidence?: AuditEvidence
}

export default function AdWarningCard({ evidence }: AdWarningCardProps) {
  if (!evidence) return null

  return (
    <section className="glass-card border-amber-300/20 bg-amber-950/15 p-4">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl border border-amber-200/20 bg-amber-300/10 text-amber-100">
          <TriangleAlert size={17} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-50">{evidence.title}</p>
          <p className="mt-1 text-xs leading-5 text-amber-50/75">{evidence.description}</p>
        </div>
      </div>
    </section>
  )
}
