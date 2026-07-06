import { motion } from 'framer-motion'
import { Eye, ShieldCheck, TriangleAlert } from 'lucide-react'
import type { AuditRecommendation, AuditVerdict } from '../types/audit'

type RecommendationCardProps = {
  recommendation: AuditRecommendation
  verdict: AuditVerdict
}

export default function RecommendationCard({ recommendation, verdict }: RecommendationCardProps) {
  const Icon = verdict === 'SAFE' ? ShieldCheck : verdict === 'CAUTION' ? Eye : TriangleAlert

  return (
    <motion.section className="glass-card border-cyan-300/15 bg-cyan-400/[0.06] p-4" layout>
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-cyan-200/20 bg-cyan-300/10 text-cyan-100">
          <Icon size={18} />
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-cyan-200/70">
            Recommendation
          </p>
          <p className="mt-1 text-base font-semibold tracking-normal text-white">{recommendation}</p>
        </div>
      </div>
    </motion.section>
  )
}
