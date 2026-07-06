import { motion } from 'framer-motion'

type SummaryCardProps = {
  summary: string
}

export default function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <motion.section className="glass-card p-4" layout>
      <p className="text-sm leading-6 text-neutral-200">{summary}</p>
    </motion.section>
  )
}
