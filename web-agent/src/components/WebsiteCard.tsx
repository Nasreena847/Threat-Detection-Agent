import { motion } from 'framer-motion'
import { Globe, Lock, Server } from 'lucide-react'
import type { ReactNode } from 'react'
import type { WebsiteInfo } from '../types/website'
import { formatScanTime } from '../utils/format'

type WebsiteCardProps = {
  website: WebsiteInfo
}

export default function WebsiteCard({ website }: WebsiteCardProps) {
  return (
    <motion.section className="glass-card p-4" layout>
      <div className="flex gap-3">
        <div className="grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-2xl border border-white/10 bg-white/[0.06]">
          {website.favicon ? (
            <img alt="" className="h-6 w-6" src={website.favicon} />
          ) : (
            <Globe className="text-neutral-300" size={18} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-white">{website.domain}</p>
          <p className="mt-0.5 line-clamp-2 text-xs leading-4 text-neutral-400">{website.title}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <InfoPill icon={<Lock size={13} />} label="HTTPS" value={website.https ? 'Enabled' : 'Disabled'} />
        <InfoPill icon={<Globe size={13} />} label="Connection" value={website.connectionType} />
        <InfoPill icon={<Server size={13} />} label="IP" value={website.ipAddress} />
        <InfoPill icon={<Globe size={13} />} label="Country" value={website.country} />
      </div>

      <p className="mt-3 text-[11px] text-neutral-500">Last scan {formatScanTime(website.lastScan)}</p>
    </motion.section>
  )
}

type InfoPillProps = {
  icon: ReactNode
  label: string
  value: string
}

function InfoPill({ icon, label, value }: InfoPillProps) {
  return (
    <div className="rounded-xl border border-white/8 bg-black/20 px-3 py-2">
      <div className="flex items-center gap-1.5 text-[11px] text-neutral-500">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-1 truncate text-xs font-medium text-neutral-200">{value}</p>
    </div>
  )
}
