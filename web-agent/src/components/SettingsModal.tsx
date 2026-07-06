import { motion } from 'framer-motion'
import { X } from 'lucide-react'
import { useState } from 'react'

type SettingsModalProps = {
  onClose: () => void
}

export default function SettingsModal({ onClose }: SettingsModalProps) {
  const [notifications, setNotifications] = useState(true)
  const [autoScan, setAutoScan] = useState(true)
  const [darkMode, setDarkMode] = useState(true)

  const handleDarkModeChange = (checked: boolean) => {
    setDarkMode(checked)
    if (checked) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('trusttab-dark-mode', 'true')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('trusttab-dark-mode', 'false')
    }
  }

  return (
    <motion.div
      animate={{ opacity: 1 }}
      className="absolute inset-0 z-20 grid place-items-center bg-black/55 p-5 backdrop-blur-sm"
      initial={{ opacity: 0 }}
    >
      <motion.section
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="glass-card w-full p-4"
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Settings</h2>
          <button className="icon-button" onClick={onClose} type="button">
            <X size={16} />
          </button>
        </div>
        <div className="mt-4 space-y-3">
          <Toggle checked={darkMode} label="Dark Mode" onChange={handleDarkModeChange} />
          <Toggle checked={notifications} label="Notifications" onChange={setNotifications} />
          <Toggle checked={autoScan} label="Auto Scan" onChange={setAutoScan} />
        </div>
        <div className="mt-5 rounded-2xl border border-white/8 bg-black/20 p-3">
          <p className="text-sm font-medium text-white">About TrustTab</p>
          <p className="mt-1 text-xs leading-5 text-neutral-400">
            AI-powered browser security assistant. Version 1.0.0.
          </p>
        </div>
      </motion.section>
    </motion.div>
  )
}

type ToggleProps = {
  checked: boolean
  label: string
  onChange: (checked: boolean) => void
}

function Toggle({ checked, label, onChange }: ToggleProps) {
  return (
    <label className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.035] px-3 py-2 text-sm text-neutral-200">
      {label}
      <input
        checked={checked}
        className="h-4 w-4 accent-emerald-300"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
    </label>
  )
}
