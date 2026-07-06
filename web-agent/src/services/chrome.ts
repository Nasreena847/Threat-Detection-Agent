import type { WebsiteInfo } from '../types/website'
import { formatDomain } from '../utils/format'

const getFavicon = (url: string, favIconUrl?: string) => {
  if (favIconUrl) return favIconUrl

  try {
    const origin = new URL(url).origin
    return `${origin}/favicon.ico`
  } catch {
    return ''
  }
}

const createWebsiteInfo = (
  url: string,
  title: string,
  favIconUrl?: string,
  pageText?: string,
  forms?: number,
  scripts?: number,
  passwordFields?: number,
  iframes?: number,
): WebsiteInfo => {
  const protocol = url.startsWith('https:') ? 'https:' : url.startsWith('http:') ? 'http:' : 'browser:'
  const now = new Date().toISOString()

  return {
    url,
    title: title || 'Untitled page',
    domain: formatDomain(url),
    protocol,
    favicon: getFavicon(url, favIconUrl),
    https: protocol === 'https:',
    connectionType: protocol === 'https:' ? 'Encrypted' : protocol === 'http:' ? 'Unencrypted' : 'Restricted',
    ipAddress: 'Pending backend lookup',
    country: 'Pending backend lookup',
    lastScan: now,
    pageText,
    forms,
    scripts,
    passwordFields,
    iframes,
  }
}

export async function getCurrentTab(): Promise<WebsiteInfo> {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })

  if (!tab?.id || !tab?.url) throw new Error('No active tab')

  const isRestrictedUrl = (url: string) => {
    return url.startsWith('chrome://') || url.startsWith('about:') || url.startsWith('edge://')
  }

  if (isRestrictedUrl(tab.url)) {
    throw new Error('Cannot analyze restricted pages (chrome://, about:*, etc.)')
  }

  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'TRUSTTAB_PAGE_METADATA',
    })

    const metadata = response as {
      url: string
      title: string
      pageText?: string
      forms?: number
      scripts?: number
      passwordFields?: number
      iframes?: number
      error?: string
    }

    if (metadata.error) {
      console.error('Content script error:', metadata.error)
      throw new Error(`Content script error: ${metadata.error}`)
    }

    return createWebsiteInfo(
      metadata.url,
      metadata.title,
      tab.favIconUrl,
      metadata.pageText,
      metadata.forms,
      metadata.scripts,
      metadata.passwordFields,
      metadata.iframes,
    )
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (message.includes('Receiving end does not exist')) {
      throw new Error('Content script is not loaded on this page. Please refresh the page.')
    }
    throw error
  }
}
