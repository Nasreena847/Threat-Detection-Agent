import { motion } from 'framer-motion'
import type { AuditEvidence } from '../types/audit'
import EvidenceCard from './EvidenceCard'

type EvidenceListProps = {
  evidence: AuditEvidence[]
}

export default function EvidenceList({ evidence }: EvidenceListProps) {
  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold tracking-normal text-white">Evidence</h2>
        <span className="text-xs text-neutral-500">{evidence.length} signals</span>
      </div>
      <motion.div className="max-h-48 space-y-2 overflow-y-auto pr-1" layout>
        {evidence.map((item, index) => (
          <motion.div
            animate={{ opacity: 1, x: 0 }}
            initial={{ opacity: 0, x: 10 }}
            key={item.id}
            transition={{ delay: index * 0.035 }}
          >
            <EvidenceCard evidence={item} />
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}
