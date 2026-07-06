import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'
import type { WebsiteInfo } from '../types/website'

type HeaderProps = {
  website?: WebsiteInfo
  backendOnline: boolean
}

export default function Header({ website, backendOnline }: HeaderProps) {
  return (
    <motion.header
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center justify-between px-4 pb-3 pt-4"
      initial={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.28 }}
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-white/10 bg-white/[0.06] text-emerald-100 shadow-lg shadow-black/30">
          <Shield size={20} />
        </div>
        <div className="min-w-0">
          <h1 className="text-base font-semibold tracking-normal text-white">TrustTab</h1>
          <p className="truncate text-xs text-neutral-400">{website?.domain ?? 'Current Website'}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] font-medium text-neutral-300">
        <span className={backendOnline ? 'status-dot' : 'status-dot status-dot-offline'} />
        {backendOnline ? 'Backend Online' : 'Backend Offline'}
      </div>
    </motion.header>
  )
}
