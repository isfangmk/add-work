import { Clock3 } from 'lucide-react'
import { APP_VERSION } from '@/constants'

export function AppHeader() {
  return (
    <header className="mb-5 flex items-center justify-between gap-4 border-b border-[#f0f0f0] pb-4">
      <div className="flex min-w-0 items-center gap-3">
        <div
          aria-hidden
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-brand-500 text-xl text-white"
        >
          <Clock3 className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="m-0 text-xl font-semibold leading-tight text-[rgba(0,0,0,0.88)]">添加工时工具</h1>
            <span className="inline-flex items-center rounded-full border border-[#ebebeb] bg-[#f5f5f5] px-2 py-0.5 text-xs leading-[18px] text-[rgba(0,0,0,0.45)] tabular-nums">
              {APP_VERSION}
            </span>
          </div>
          <p className="mt-0.5 text-[13px] leading-normal text-[rgba(0,0,0,0.45)]">批量填报工时，支持 AI 帮写</p>
        </div>
      </div>
    </header>
  )
}
