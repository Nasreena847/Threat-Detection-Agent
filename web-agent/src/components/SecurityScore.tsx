import { animate, motion, useMotionValue, useTransform } from 'framer-motion'
import { ShieldCheck, TriangleAlert } from 'lucide-react'
import { useEffect } from 'react'
import { verdictColors } from '../constants/colors'
import type { AuditVerdict } from '../types/audit'

type SecurityScoreProps = {
  score: number
  verdict: AuditVerdict
}

export default function SecurityScore({ score, verdict }: SecurityScoreProps) {
  const animatedScore = useMotionValue(0)
  const displayScore = useTransform(animatedScore, (value) => Math.round(value))
  const tone = verdictColors[verdict]
  const Icon = verdict === 'SAFE' ? ShieldCheck : TriangleAlert

  useEffect(() => {
    const controls = animate(animatedScore, score, {
      duration: 0.85,
      ease: 'easeOut',
    })

    return controls.stop
  }, [animatedScore, score])

  return (
    <motion.section className="glass-card p-4" layout>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-neutral-500">
            Security Score
          </p>
          <p className={`mt-1 text-sm font-semibold ${tone.text}`}>{verdict}</p>
        </div>
        <div className={`rounded-2xl border ${tone.border} bg-white/[0.04] p-2 ${tone.text}`}>
          <Icon size={18} />
        </div>
      </div>

      <div className="mt-5 grid place-items-center">
        <motion.div
          animate={{ scale: 1, opacity: 1 }}
          className={`score-orb bg-gradient-to-br ${tone.gradient} shadow-2xl ${tone.glow}`}
          initial={{ scale: 0.9, opacity: 0 }}
        >
          <div className="grid h-32 w-32 place-items-center rounded-full bg-neutral-950 shadow-inner shadow-black/70">
            <div className="text-center">
              <motion.p className="text-5xl font-semibold tabular-nums tracking-normal text-white">
                {displayScore}
              </motion.p>
              <p className={`mt-1 text-xs font-bold tracking-[0.2em] ${tone.text}`}>{verdict}</p>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.section>
  )
}
