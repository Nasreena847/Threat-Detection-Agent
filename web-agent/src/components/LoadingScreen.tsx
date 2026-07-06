import { useEffect, useState } from 'react'
import SkeletonLoader from './SkeletonLoader'

const messages = [
  'Connecting...',
  'Reading Website...',
  'Checking HTTPS...',
  'Inspecting Scripts...',
  'Analyzing Privacy...',
  'Generating Report...',
  'Almost Done...',
]

export default function LoadingScreen() {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    const interval = window.setInterval(() => {
      setMessageIndex((current) => (current + 1) % messages.length)
    }, 1_000)

    return () => window.clearInterval(interval)
  }, [])

  return (
    <section className="space-y-4">
      <div className="glass-card p-4 text-center">
        <div className="loader-rings mx-auto">
          <span />
          <span />
          <span />
        </div>
        <p className="mt-5 text-sm font-semibold text-white">{messages[messageIndex]}</p>
      </div>
      <SkeletonLoader />
    </section>
  )
}
