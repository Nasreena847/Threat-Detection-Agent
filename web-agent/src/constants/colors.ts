import type { AuditVerdict } from '../types/audit'

export const verdictColors: Record<
  AuditVerdict,
  {
    text: string
    glow: string
    border: string
    gradient: string
  }
> = {
  SAFE: {
    text: 'text-emerald-200',
    glow: 'shadow-emerald-950/50',
    border: 'border-emerald-300/20',
    gradient: 'from-emerald-300 via-teal-300 to-cyan-300',
  },
  CAUTION: {
    text: 'text-amber-200',
    glow: 'shadow-amber-950/50',
    border: 'border-amber-300/20',
    gradient: 'from-amber-300 via-orange-300 to-rose-300',
  },
  RISKY: {
    text: 'text-red-200',
    glow: 'shadow-red-950/50',
    border: 'border-red-300/20',
    gradient: 'from-red-300 via-rose-300 to-orange-300',
  },
}
