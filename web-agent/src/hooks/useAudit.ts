import { useQuery, useQueryClient } from '@tanstack/react-query'
import { auditWebsite } from '../services/api'
import { getCurrentTab } from '../services/chrome'
import type { AuditReport } from '../types/audit'
import type { WebsiteInfo } from '../types/website'

const previewAudit: AuditReport = {
  score: 8,
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

export function useAudit(website?: WebsiteInfo, enabled = true) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: [
      'audit',
      website?.url,
      website?.forms,
      website?.scripts,
      website?.passwordFields,
      website?.iframes,
      website?.ads,
    ],
    enabled: Boolean(website) && enabled,
    staleTime: 0,
    refetchOnMount: 'always',
    retry: 1,
    queryFn: async () => {
      const currentWebsite = await getCurrentTab().catch(() => website)

      if (!currentWebsite || !canAudit(currentWebsite)) {
        return previewAudit
      }

      return auditWebsite({
        url: currentWebsite.url,
        domain: currentWebsite.domain,
        title: currentWebsite.title,
        favicon: currentWebsite.favicon,
        https: currentWebsite.https,
        page_text: currentWebsite.pageText || '',
        forms: currentWebsite.forms,
        scripts: currentWebsite.scripts,
        password_fields: currentWebsite.passwordFields,
        iframes: currentWebsite.iframes,
        ads: currentWebsite.ads,
      })
    },
  })

  const refresh = async () => {
    if (website && canAudit(website)) {
      await query.refetch()
      return
    }

    await queryClient.invalidateQueries({ queryKey: ['audit'] })
  }

  return {
    ...query,
    audit: query.data ?? null,
    refresh,
  }
}
