import { TriangleAlert } from 'lucide-react'

type ErrorCardProps = {
  message: string
  onRetry: () => void
  showLocalSetup?: boolean
}

const localSetupCommands = [
  'cd backend',
  'python3 -m venv venv',
  'source venv/bin/activate',
  'pip install -r requirements.txt',
  'cp .env.example .env',
  'uvicorn app.main:app --reload',
]

export default function ErrorCard({ message, onRetry, showLocalSetup = false }: ErrorCardProps) {
  return (
    <section className="glass-card border-red-300/15 bg-red-400/[0.07] p-4">
      <div className="flex gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-red-200/20 bg-red-300/10 text-red-100">
          <TriangleAlert size={18} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white">Analysis unavailable</p>
          <p className="mt-1 text-xs leading-5 text-red-100/75">{message}</p>
          {showLocalSetup ? (
            <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
              <p className="text-xs font-semibold text-white">Free-tier API unavailable?</p>
              <p className="mt-1 text-xs leading-5 text-red-100/70">
                Start the FastAPI backend locally, then keep this extension pointed to
                http://localhost:8000/api/audit.
              </p>
              <div className="mt-2 space-y-1">
                {localSetupCommands.map((command) => (
                  <code
                    className="block overflow-x-auto rounded-lg bg-black/35 px-2 py-1 text-[10px] leading-4 text-red-50/85"
                    key={command}
                  >
                    {command}
                  </code>
                ))}
              </div>
              <p className="mt-2 text-[10px] leading-4 text-red-100/60">
                Windows venv activation: venv\Scripts\activate. API docs:
                http://127.0.0.1:8000/docs.
              </p>
            </div>
          ) : null}
          <button className="mt-3 footer-button h-8 px-3" onClick={onRetry} type="button">
            Retry
          </button>
        </div>
      </div>
    </section>
  )
}
