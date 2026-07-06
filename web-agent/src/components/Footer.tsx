import { Eye, RefreshCw, Settings } from 'lucide-react'

type FooterProps = {
  isRefreshing: boolean
  onRefresh: () => void
  onSettings: () => void
  onDetails: () => void
}

export default function Footer({ isRefreshing, onRefresh, onSettings, onDetails }: FooterProps) {
  return (
    <footer className="grid grid-cols-3 gap-2 border-t border-white/10 bg-neutral-950/85 p-3 backdrop-blur-xl">
      <button className="footer-button" disabled={isRefreshing} onClick={onRefresh} type="button">
        <RefreshCw className={isRefreshing ? 'animate-spin' : ''} size={15} />
        Refresh
      </button>
      <button className="footer-button" onClick={onDetails} type="button">
        <Eye size={15} />
        Details
      </button>
      <button className="footer-button" onClick={onSettings} type="button">
        <Settings size={15} />
        Settings
      </button>
    </footer>
  )
}
