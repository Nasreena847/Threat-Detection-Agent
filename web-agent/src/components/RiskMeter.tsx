import { motion } from 'framer-motion'

type RiskMeterProps = {
  score: number
}

export default function RiskMeter({ score }: RiskMeterProps) {
  const riskyPosition = 100 - score

  return (
    <motion.section className="glass-card p-4" layout>
      <div className="flex items-center justify-between text-xs text-neutral-400">
        <span>Safe</span>
        <span>Caution</span>
        <span>Risky</span>
      </div>
      <div className="relative mt-3 h-4 rounded-full border border-white/10 bg-gradient-to-r from-emerald-300 via-amber-300 to-red-400 p-0.5">
        <div className="h-full rounded-full bg-black/25" />
        <motion.span
          animate={{ left: `${riskyPosition}%` }}
          className="risk-needle"
          initial={false}
          transition={{ type: 'spring', stiffness: 220, damping: 24 }}
        />
      </div>
    </motion.section>
  )
}
