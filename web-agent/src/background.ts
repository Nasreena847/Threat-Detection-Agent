import { auditWebsite } from './services/api'
import type { AuditRequest } from './types/audit'
import { formatDomain } from './utils/format'

const AUTO_SCAN_STORAGE_KEY = 'trusttab-auto-scan'
const LATEST_AUDIT_STORAGE_KEY = 'trusttab-latest-audit'
const AUTO_SCAN_DEBOUNCE_MS = 1200
const pendingScans = new Map<number, number>()

type PageMetadata = {
  ads?: number
  error?: string
  forms?: number
  iframes?: number
  pageText?: string
  passwordFields?: number
  scripts?: number
  title?: string
  url?: string
}

const isHttpUrl = (url?: string) => Boolean(url?.startsWith('http://') || url?.startsWith('https://'))

const isAutoScanEnabled = async () => {
  const stored = await chrome.storage.local.get(AUTO_SCAN_STORAGE_KEY)
  return stored[AUTO_SCAN_STORAGE_KEY] !== false
}

const metadataToAuditRequest = (metadata: PageMetadata, fallbackUrl: string, fallbackTitle = ''): AuditRequest => {
  const url = metadata.url || fallbackUrl

  return {
    url,
    domain: formatDomain(url),
    title: metadata.title || fallbackTitle,
    favicon: '',
    https: url.startsWith('https://'),
    page_text: metadata.pageText || '',
    forms: metadata.forms,
    scripts: metadata.scripts,
    password_fields: metadata.passwordFields,
    iframes: metadata.iframes,
    ads: metadata.ads,
  }
}

const runAutoScan = async (tabId: number, tab: ChromeTab) => {
  if (!isHttpUrl(tab.url) || !(await isAutoScanEnabled())) return

  try {
    const metadata = (await chrome.tabs.sendMessage(tabId, {
      type: 'TRUSTTAB_PAGE_METADATA',
    })) as PageMetadata

    if (metadata.error) {
      throw new Error(metadata.error)
    }

    const payload = metadataToAuditRequest(metadata, tab.url || '', tab.title || '')
    const report = await auditWebsite(payload)
    await chrome.storage.local.set({
      [LATEST_AUDIT_STORAGE_KEY]: {
        payload,
        report,
        scannedAt: new Date().toISOString(),
      },
    })
  } catch (error) {
    console.warn('TrustTab auto scan failed:', error)
  }
}

chrome.runtime.onInstalled.addListener(() => {
  void chrome.storage.local.set({
    trusttabInstalledAt: new Date().toISOString(),
    [AUTO_SCAN_STORAGE_KEY]: true,
  })
})

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== 'complete' || !isHttpUrl(tab.url)) return

  const existing = pendingScans.get(tabId)
  if (existing) {
    clearTimeout(existing)
  }

  const timeoutId = globalThis.setTimeout(() => {
    pendingScans.delete(tabId)
    void runAutoScan(tabId, tab)
  }, AUTO_SCAN_DEBOUNCE_MS)

  pendingScans.set(tabId, timeoutId)
})
