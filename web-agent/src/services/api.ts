import type {
  AuditEvidence,
  AuditHistoryEntry,
  AuditReport,
  AuditRequest,
  EvidenceStatus,
} from '../types/audit'
import { clampScore, getRecommendation, getVerdict } from '../utils/score'

const API_URL = 'http://127.0.0.1:8000/api/audit'
const LOCAL_BACKEND_URL = 'http://127.0.0.1:8000'
const CACHE_VERSION = 'v2'
const HISTORY_STORAGE_KEY = `trusttab:audit:${CACHE_VERSION}:history`
const MAX_HISTORY_ITEMS = 8

type BackendEvidence = {
  id?: unknown
  title?: unknown
  label?: unknown
  description?: unknown
  status?: unknown
  icon?: unknown
}

type BackendAuditResponse = {
  scan_id?: unknown
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
  components?: unknown
  threat_intel?: unknown
  ml?: unknown
  explanation_source?: unknown
}

type BackendHistoryResponse = {
  scans?: unknown
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
  const raw = window.localStorage.getItem(`trusttab:audit:${CACHE_VERSION}:${domain}`)
  if (!raw) return null

  try {
    return JSON.parse(raw) as AuditReport
  } catch {
    return null
  }
}

export const readAuditHistory = (): AuditHistoryEntry[] => {
  if (typeof window === 'undefined') return []

  const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY)
  if (!raw) return []

  try {
    const parsed = JSON.parse(raw) as AuditHistoryEntry[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const writeCachedAudit = (domain: string, report: AuditReport) => {
  window.localStorage.setItem(`trusttab:audit:${CACHE_VERSION}:${domain}`, JSON.stringify(report))
}

const writeAuditHistory = (payload: AuditRequest, report: AuditReport) => {
  if (typeof window === 'undefined') return

  const entry: AuditHistoryEntry = {
    domain: payload.domain ?? payload.url,
    url: payload.url,
    score: report.score,
    verdict: report.verdict,
    timestamp: new Date().toISOString(),
    summary: report.summary,
  }

  const existing = readAuditHistory().filter((item) => item.url !== payload.url)
  const nextHistory = [entry, ...existing].slice(0, MAX_HISTORY_ITEMS)
  window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(nextHistory))
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null

const domainFromUrl = (url: string) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

const normalizeHistoryItem = (item: unknown): AuditHistoryEntry | null => {
  if (!isRecord(item)) return null

  const report = isRecord(item.report) ? item.report : {}
  const score = clampScore(item.risk_score ?? report.risk_score ?? report.score)
  const verdict = normalizeVerdict(item.risk_level ?? report.risk_level ?? report.verdict, score)
  const url = String(item.url ?? report.url ?? '')

  if (!url) return null

  return {
    id: typeof item.id === 'number' ? item.id : undefined,
    domain: String(item.domain ?? domainFromUrl(url)),
    url,
    score,
    verdict,
    timestamp: String(item.created_at ?? new Date().toISOString()),
    summary: String(report.explanation ?? report.summary ?? 'Scan completed.'),
  }
}

export async function fetchAuditHistory(limit = 8): Promise<AuditHistoryEntry[]> {
  try {
    const response = await fetch(`${API_URL}/history?limit=${limit}`)
    if (!response.ok) return readAuditHistory()

    const data = (await response.json()) as BackendHistoryResponse
    if (!Array.isArray(data.scans)) return readAuditHistory()

    const history = data.scans
      .map((item) => normalizeHistoryItem(item))
      .filter((item): item is AuditHistoryEntry => item !== null)

    return history.length > 0 ? history : readAuditHistory()
  } catch {
    return readAuditHistory()
  }
}

export async function auditWebsite(payload: AuditRequest): Promise<AuditReport> {
  let response: Response

  try {
    response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch {
    const cached = readCachedAudit(payload.domain)
    if (cached) return cached
    throw new Error(
      `The local audit API is unreachable. Start the backend at ${LOCAL_BACKEND_URL} and retry.`,
    )
  }

  if (!response.ok) {
    const cached = readCachedAudit(payload.domain)
    if (cached) return cached
    throw new Error(
      `Audit service returned ${response.status}. Start the backend at ${LOCAL_BACKEND_URL} and retry.`,
    )
  }

  const data = (await response.json()) as BackendAuditResponse
  const reasons = normalizeReasons(data.reasons)
  const score = clampScore(data.risk_score ?? data.score)
  const verdict = normalizeVerdict(data.risk_level ?? data.verdict, score)
  const evidence = buildEvidence(data.evidence, reasons)

  const report: AuditReport = {
    scanId: typeof data.scan_id === 'number' ? data.scan_id : undefined,
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
    components: isRecord(data.components) ? data.components : undefined,
    threatIntel: isRecord(data.threat_intel) ? data.threat_intel : undefined,
    ml: isRecord(data.ml) ? data.ml : undefined,
    explanationSource: isRecord(data.explanation_source) ? data.explanation_source : undefined,
  }

  writeCachedAudit(payload.domain, report)
  writeAuditHistory(payload, report)
  return report
}

