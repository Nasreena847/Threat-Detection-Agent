import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import { fetchAuditHistory, readAuditHistory } from '../services/api'

document.documentElement.classList.add('history-page-root')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
})

const formatTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Recent'

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function HistoryPage() {
  const historyQuery = useQuery({
    queryKey: ['audit-history-page'],
    queryFn: () => fetchAuditHistory(100),
    initialData: readAuditHistory,
    staleTime: 10_000,
  })

  return (
    <main className="history-page-shell">
      <section className="history-page-header">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-200/70">
            TrustTab
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-normal text-white">Scan history</h1>
        </div>
        <button className="footer-button px-4" onClick={() => void historyQuery.refetch()} type="button">
          Refresh
        </button>
      </section>

      <section className="history-page-list">
        {historyQuery.data.length > 0 ? (
          historyQuery.data.map((item) => (
            <article className="history-page-card" key={`${item.id ?? item.url}-${item.timestamp}`}>
              <div className="flex min-w-0 items-start justify-between gap-4">
                <div className="min-w-0">
                  <h2 className="truncate text-base font-semibold text-white">{item.domain}</h2>
                  <p className="mt-1 break-all text-xs text-neutral-500">{item.url}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-right">
                  <p className="text-lg font-semibold tabular-nums text-white">{item.score}%</p>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-neutral-500">
                    {item.verdict}
                  </p>
                </div>
              </div>
              <p className="mt-3 text-xs text-neutral-500">{formatTime(item.timestamp)}</p>
              <p className="mt-3 text-sm leading-6 text-neutral-300">{item.summary}</p>
            </article>
          ))
        ) : (
          <div className="glass-card p-5 text-sm text-neutral-400">No scan history yet.</div>
        )}
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <HistoryPage />
    </QueryClientProvider>
  </StrictMode>,
)
