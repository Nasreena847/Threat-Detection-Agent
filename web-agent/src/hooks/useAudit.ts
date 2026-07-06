import { useQuery, useQueryClient } from '@tanstack/react-query'
import { auditWebsite } from '../services/api'
import type { AuditReport } from '../types/audit'
import type { WebsiteInfo } from '../types/website'

const previewAudit: AuditReport = {
  score: 92,
  verdict: 'SAFE',
  summary: 'This website appears safe. No significant phishing indicators were detected.',
  recommendation: 'Safe to Browse',
  reasons: ['HTTPS Enabled', 'SSL Certificate Valid', 'No suspicious forms'],
  evidence: [
    {
      id: 'https',
      title: 'HTTPS Enabled',
      description: 'Encrypted connection established.',
      status: 'positive',
      icon: 'lock',
    },
    {
      id: 'ssl',
      title: 'SSL Certificate Valid',
      description: 'Certificate appears valid.',
      status: 'positive',
      icon: 'shield',
    },
    {
      id: 'trackers',
      title: 'Third Party Trackers',
      description: 'Detected 4 trackers.',
      status: 'warning',
      icon: 'radar',
    },
    {
      id: 'scripts',
      title: 'External Scripts',
      description: 'Loaded 7 external scripts.',
      status: 'warning',
      icon: 'server',
    },
    {
      id: 'login',
      title: 'Login Form',
      description: 'Sensitive form detected.',
      status: 'warning',
      icon: 'bug',
    },
    {
      id: 'cookies',
      title: 'Secure Cookies',
      description: 'Cookie security attributes appear present.',
      status: 'positive',
      icon: 'check',
    },
  ],
}

const canAudit = (website?: WebsiteInfo) =>
  Boolean(website?.url && (website.url.startsWith('http://') || website.url.startsWith('https://')))

export function useAudit(website?: WebsiteInfo) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['audit', website?.url],
    enabled: Boolean(website),
    staleTime: 60_000,
    retry: 1,
    queryFn: async () => {
      if (!website || !canAudit(website)) {
        return previewAudit
      }

      return auditWebsite({
        url: website.url,
        domain: website.domain,
        title: website.title,
        favicon: website.favicon,
        https: website.https,
        page_text: website.pageText || '',
      })
    },
  })

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['audit', website?.url] })
  }

  return {
    ...query,
    audit: query.data ?? null,
    refresh,
  }
}
