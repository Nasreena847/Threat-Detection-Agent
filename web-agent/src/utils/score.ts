import type { AuditRecommendation, AuditVerdict } from '../types/audit'

export const clampScore = (score: unknown) => Math.max(0, Math.min(Number(score ?? 0), 100))

export const getVerdict = (score: number, value?: string): AuditVerdict => {
  const normalized = value?.toUpperCase()

  if (normalized === 'SAFE' || normalized === 'CAUTION' || normalized === 'RISKY') {
    return normalized
  }

  if (score <= 25) return 'SAFE'
  if (score <= 60) return 'CAUTION'
  return 'RISKY'
}

export const getRecommendation = (score: number, value?: string): AuditRecommendation => {
  if (value) return value
  if (score <= 25) return 'Safe to Browse'
  if (score <= 45) return 'Browse Only'
  if (score <= 60) return 'Avoid Login'
  if (score <= 80) return 'Avoid Payments'
  return 'Leave Immediately'
}
