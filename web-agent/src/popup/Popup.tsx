import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import AnalysisTimeline from '../components/AnalysisTimeline'
import ErrorCard from '../components/ErrorCard'
import EvidenceList from '../components/EvidenceList'
import Footer from '../components/Footer'
import Header from '../components/Header'
import LoadingScreen from '../components/LoadingScreen'
import RecommendationCard from '../components/RecommendationCard'
import RiskMeter from '../components/RiskMeter'
import SecurityScore from '../components/SecurityScore'
import SettingsModal from '../components/SettingsModal'
import SummaryCard from '../components/SummaryCard'
import WebsiteCard from '../components/WebsiteCard'
import { useAudit } from '../hooks/useAudit'
import { useCurrentTab } from '../hooks/useCurrentTab'

export default function Popup() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [detailsExpanded, setDetailsExpanded] = useState(false)
  const currentTab = useCurrentTab()
  const website = currentTab.data
  const auditQuery = useAudit(website)
  const audit = auditQuery.audit
  const isLoading = currentTab.isLoading || auditQuery.isLoading
  const errorMessage =
    currentTab.error instanceof Error
      ? currentTab.error.message
      : auditQuery.error instanceof Error
        ? auditQuery.error.message
        : ''

  const handleRefresh = () => {
    void currentTab.refetch()
    void auditQuery.refresh()
  }

  return (
    <main className="trusttab-shell">
      <div className="absolute inset-x-0 top-0 h-64 bg-[radial-gradient(circle_at_22%_0%,rgba(45,212,191,0.16),transparent_34%),radial-gradient(circle_at_82%_8%,rgba(244,114,182,0.1),transparent_28%)]" />
      <section className="relative flex h-full flex-col overflow-hidden rounded-[28px] border border-white/10 bg-neutral-950/92 shadow-2xl shadow-black/60">
        <Header backendOnline={!auditQuery.isError} website={website} />

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                initial={{ opacity: 0, y: 8 }}
                key="loading"
              >
                <LoadingScreen />
              </motion.div>
            ) : (
              <motion.div
                animate={{ opacity: 1, y: 0 }}
                className="space-y-3"
                exit={{ opacity: 0, y: -8 }}
                initial={{ opacity: 0, y: 8 }}
                key="report"
              >
                {errorMessage ? (
                  <ErrorCard
                    message={errorMessage}
                    onRetry={handleRefresh}
                    showLocalSetup={auditQuery.error instanceof Error}
                  />
                ) : null}
                {website ? <WebsiteCard website={website} /> : null}
                {audit ? (
                  <>
                    <SecurityScore score={audit.score} verdict={audit.verdict} />
                    <RiskMeter score={audit.score} />
                    <SummaryCard summary={audit.summary} />
                    {detailsExpanded ? <EvidenceList evidence={audit.evidence} /> : null}
                    <RecommendationCard
                      recommendation={audit.recommendation}
                      verdict={audit.verdict}
                    />
                    <AnalysisTimeline />
                  </>
                ) : null}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <Footer
          isRefreshing={currentTab.isFetching || auditQuery.isFetching}
          onDetails={() => setDetailsExpanded(!detailsExpanded)}
          onRefresh={handleRefresh}
          onSettings={() => setSettingsOpen(true)}
        />

        <AnimatePresence>
          {settingsOpen ? <SettingsModal onClose={() => setSettingsOpen(false)} /> : null}
        </AnimatePresence>
      </section>
    </main>
  )
}
