import type { ReactNode } from 'react'

interface SectionProps {
  step: number | string
  title: string
  description?: ReactNode
  children: ReactNode
  action?: ReactNode
}

export function Section({ step, title, description, children, action }: SectionProps) {
  return (
    <section className="overflow-hidden rounded-[10px] border border-[#f0f0f0] bg-white">
      <div className="flex items-start justify-between gap-3 border-b border-[#f0f0f0] bg-[#fafafa] px-4 py-3.5">
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-px inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500 text-xs font-semibold leading-none text-white">
            {step}
          </span>
          <div className="min-w-0">
            <h2 className="m-0 text-[15px] font-semibold leading-normal text-[rgba(0,0,0,0.88)]">{title}</h2>
            {description && <p className="mt-0.5 text-xs leading-relaxed text-[rgba(0,0,0,0.45)]">{description}</p>}
          </div>
        </div>
        {action && <div className="shrink-0 pt-0.5">{action}</div>}
      </div>
      <div className="bg-[#f8f9fa] p-4">{children}</div>
    </section>
  )
}
