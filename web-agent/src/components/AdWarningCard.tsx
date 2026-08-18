import { TriangleAlert } from 'lucide-react'
import type { AuditEvidence } from '../types/audit'

type AdWarningCardProps = {
  adRisk?: Record<string, unknown>
  evidence?: AuditEvidence
}

export default function AdWarningCard({ adRisk, evidence }: AdWarningCardProps) {
  const adCount = Number(adRisk?.count ?? 0)
  const adScore = Number(adRisk?.score ?? 0)
  const severity = String(adRisk?.severity ?? 'none')
  if (!evidence && adScore <= 0) return null

  const title = evidence?.title ?? 'Ad Risk Model Signal'
  const description =
    evidence?.description ??
    `The ad risk model found ${adCount} ad-like element(s) and rated the ad risk as ${severity}. Ads from unknown networks can be unreliable and may lead to scam, malware, or virus-like redirects.`

  return (
    <section className="glass-card border-amber-300/20 bg-amber-950/15 p-4">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl border border-amber-200/20 bg-amber-300/10 text-amber-100">
          <TriangleAlert size={17} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-50">{title}</p>
          <p className="mt-1 text-xs leading-5 text-amber-50/75">{description}</p>
        </div>
      </div>
    </section>
  )
}
