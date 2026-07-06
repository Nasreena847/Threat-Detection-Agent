import { motion } from 'framer-motion'
import { CircleCheck } from 'lucide-react'

const steps = ['Connection', 'Metadata', 'Scripts', 'Trackers', 'Risk Analysis', 'Completed']

export default function AnalysisTimeline() {
  return (
    <section className="glass-card p-4">
      <h2 className="text-sm font-semibold text-white">Analysis Timeline</h2>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {steps.map((step, index) => (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-white/8 bg-white/[0.035] px-2 py-2 text-center"
            initial={{ opacity: 0, y: 8 }}
            key={step}
            transition={{ delay: index * 0.045 }}
          >
            <CircleCheck className="mx-auto text-emerald-200" size={14} />
            <p className="mt-1 truncate text-[11px] text-neutral-400">{step}</p>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
