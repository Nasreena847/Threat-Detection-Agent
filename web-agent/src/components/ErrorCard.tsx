import { TriangleAlert } from 'lucide-react'

type ErrorCardProps = {
  message: string
  onRetry: () => void
}

export default function ErrorCard({ message, onRetry }: ErrorCardProps) {
  return (
    <section className="glass-card border-red-300/15 bg-red-400/[0.07] p-4">
      <div className="flex gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-red-200/20 bg-red-300/10 text-red-100">
          <TriangleAlert size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Analysis unavailable</p>
          <p className="mt-1 text-xs leading-5 text-red-100/75">{message}</p>
          <button className="mt-3 footer-button h-8 px-3" onClick={onRetry} type="button">
            Retry
          </button>
        </div>
      </div>
    </section>
  )
}
