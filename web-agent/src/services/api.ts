import type { AuditEvidence, AuditReport, AuditRequest, EvidenceStatus } from '../types/audit'
import { clampScore, getRecommendation, getVerdict } from '../utils/score'

const API_URL = 'http://localhost:8000/api/audit'

type BackendEvidence = {
  id?: unknown
  title?: unknown
  label?: unknown
  description?: unknown
  status?: unknown
  icon?: unknown
}

type BackendAuditResponse = {
  risk_score?: unknown
  risk_level?: unknown
  explanation?: unknown
  recommendation?: unknown
  reasons?: unknown
  evidence?: unknown
  score?: unknown
  verdict?: unknown
  summary?: unknown
  website?: unknown
}

const isEvidenceStatus = (value: unknown): value is EvidenceStatus =>
  value === 'positive' || value === 'warning' || value === 'negative'

const isEvidenceIcon = (value: unknown): value is NonNullable<AuditEvidence['icon']> =>
  value === 'lock' ||
  value === 'shield' ||
  value === 'radar' ||
  value === 'server' ||
  value === 'bug' ||
  value === 'check' ||
  value === 'alert'

const normalizeEvidenceItem = (item: unknown, index: number): AuditEvidence | null => {
  if (typeof item === 'string') {
    const isPositive =
      item.toLowerCase().includes('enabled') ||
      item.toLowerCase().includes('valid') ||
      item.toLowerCase().includes('secure')

    return {
      id: `evidence-${index}`,
      title: item.replace(/^[✔⚠]\s*/, ''),
      description: isPositive ? 'No issue detected for this signal.' : 'Review this signal before proceeding.',
      status: isPositive ? 'positive' : 'warning',
    }
  }

  if (!item || typeof item !== 'object') return null

  const evidence = item as BackendEvidence
  const title = String(evidence.title ?? evidence.label ?? `Security signal ${index + 1}`)
  const status = isEvidenceStatus(evidence.status) ? evidence.status : 'warning'

  return {
    id: String(evidence.id ?? `evidence-${index}`),
    title,
    description: String(evidence.description ?? 'Security signal returned by the audit service.'),
    status,
    icon: isEvidenceIcon(evidence.icon) ? evidence.icon : undefined,
  }
}

const normalizeEvidence = (value: unknown): AuditEvidence[] => {
  if (!Array.isArray(value)) return []

  return value
    .map((item, index) => normalizeEvidenceItem(item, index))
    .filter((item): item is AuditEvidence => item !== null)
}

const normalizeReasons = (value: unknown): string[] =>
  Array.isArray(value) ? value.map((reason) => String(reason)) : []

const normalizeVerdict = (value: unknown, score: number): AuditReport['verdict'] => {
  const normalized = typeof value === 'string' ? value.trim().toLowerCase() : ''

  if (normalized === 'safe' || normalized === 'low') return 'SAFE'
  if (normalized === 'medium' || normalized === 'caution' || normalized === 'warning') return 'CAUTION'
  if (normalized === 'high' || normalized === 'risky' || normalized === 'danger') return 'RISKY'

  return getVerdict(score)
}

const buildEvidence = (value: unknown, reasons: string[]): AuditEvidence[] => {
  const fromBackend = normalizeEvidence(value)
  if (fromBackend.length > 0) return fromBackend

  return reasons.map((reason, index) => ({
    id: `evidence-${index}`,
    title: reason,
    description: 'Reason provided by the backend audit service.',
    status: 'warning' as const,
  }))
}

const readCachedAudit = (domain: string): AuditReport | null => {
  const raw = window.localStorage.getItem(`trusttab:audit:${domain}`)
  if (!raw) return null

  try {
    return JSON.parse(raw) as AuditReport
  } catch {
    return null
  }
}

const writeCachedAudit = (domain: string, report: AuditReport) => {
  window.localStorage.setItem(`trusttab:audit:${domain}`, JSON.stringify(report))
}

export async function auditWebsite(payload: AuditRequest): Promise<AuditReport> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const cached = readCachedAudit(payload.domain)
    if (cached) return cached
    throw new Error(`Audit service returned ${response.status}`)
  }

  const data = (await response.json()) as BackendAuditResponse
  const reasons = normalizeReasons(data.reasons)
  const score = clampScore(data.risk_score ?? data.score)
  const verdict = normalizeVerdict(data.risk_level ?? data.verdict, score)
  const evidence = buildEvidence(data.evidence, reasons)

  const report: AuditReport = {
    score,
    verdict,
    summary:
      typeof data.explanation === 'string'
        ? data.explanation
        : typeof data.summary === 'string'
          ? data.summary
          : 'TrustTab received a report, but no summary was provided.',
    recommendation: getRecommendation(
      score,
      typeof data.recommendation === 'string' ? data.recommendation : undefined,
    ),
    reasons,
    evidence,
    website: data.website && typeof data.website === 'object' ? data.website : undefined,
  }

  writeCachedAudit(payload.domain, report)
  return report
}
