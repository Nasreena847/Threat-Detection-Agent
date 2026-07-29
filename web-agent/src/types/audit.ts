import type { WebsiteInfo } from './website'

export type AuditVerdict = 'SAFE' | 'CAUTION' | 'RISKY'

export type EvidenceStatus = 'positive' | 'warning' | 'negative'

export type AuditEvidence = {
  id: string
  title: string
  description: string
  status: EvidenceStatus
  icon?: 'lock' | 'shield' | 'radar' | 'server' | 'bug' | 'check' | 'alert'
}

export type AuditRecommendation =
  | 'Safe to Browse'
  | 'Browse Only'
  | 'Avoid Login'
  | 'Avoid Payments'
  | 'Leave Immediately'
  | string

export type AuditReport = {
  score: number
  verdict: AuditVerdict
  summary: string
  recommendation: AuditRecommendation
  reasons: string[]
  evidence: AuditEvidence[]
  website?: Partial<WebsiteInfo>
}

export type AuditRequest = {
  url: string
  domain: string
  title: string
  favicon: string
  https: boolean
  page_text?: string
  forms?: number
  scripts?: number
  password_fields?: number
  iframes?: number
}
