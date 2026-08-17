import { ChevronDown, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import type { AuditHistoryEntry } from '../types/audit'

type ScanHistoryProps = {
  history: AuditHistoryEntry[]
  limit?: number
}

const formatTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Recent'

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

const openHistoryPage = () => {
  const historyUrl =
    typeof chrome !== 'undefined' && chrome.runtime?.getURL
      ? chrome.runtime.getURL('history.html')
      : 'history.html'

  if (typeof chrome !== 'undefined' && chrome.tabs?.create) {
    void chrome.tabs.create({ url: historyUrl })
    return
  }

  window.open(historyUrl, '_blank', 'noopener,noreferrer')
}

export default function ScanHistory({ history, limit = 5 }: ScanHistoryProps) {
  const [expanded, setExpanded] = useState(false)
  const visibleHistory = history.slice(0, limit)
  const hasMore = history.length > limit

  return (
    <section className="glass-card overflow-hidden">
      <button
        aria-expanded={expanded}
        className="details-trigger"
        onClick={() => setExpanded((current) => !current)}
        type="button"
      >
        <span>
          <span className="block text-sm font-semibold text-white">Scan history</span>
          <span className="text-xs text-neutral-500">{history.length} scans recorded</span>
        </span>
        <ChevronDown
          className={expanded ? 'details-chevron details-chevron-open' : 'details-chevron'}
          size={18}
        />
      </button>

      {expanded ? (
        <div className="history-panel">
          {history.length > 0 ? (
            <div className="space-y-2">
              {visibleHistory.map((item) => (
                <article
                  className="rounded-xl border border-white/10 bg-black/20 px-3 py-2"
                  key={`${item.id ?? item.url}-${item.timestamp}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium text-white">{item.domain}</p>
                    <span className="text-[11px] tabular-nums text-white/70">{item.score}%</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between gap-2 text-[11px] text-white/55">
                    <span>{item.verdict}</span>
                    <span>{formatTime(item.timestamp)}</span>
                  </div>
                  <p className="mt-1 text-[11px] leading-4 text-white/55">{item.summary}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="rounded-xl border border-white/8 bg-black/20 px-3 py-2 text-xs text-neutral-500">
              No scans recorded yet.
            </p>
          )}

          {hasMore ? (
            <button className="show-more-button" onClick={openHistoryPage} type="button">
              Show more
              <ExternalLink size={13} />
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
