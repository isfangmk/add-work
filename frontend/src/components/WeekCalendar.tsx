import { forwardRef, useImperativeHandle, useRef } from 'react'
import { Inbox, Pencil, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { format, addDays } from 'date-fns'
import { cn } from '@/lib/utils'
import type { CalendarData, FavoriteWorkspace, WorkItem } from '@/types'

export interface WeekCalendarRef {
  scrollToRight: () => void
}

interface WeekCalendarProps {
  calendarData: CalendarData
  monday: Date
  sourceItem: WorkItem | null
  onSelect: (item: WorkItem) => void
  onEdit: (item: WorkItem) => void
  loading: boolean
  error: string | null
  favorites: FavoriteWorkspace[]
  onOpenFavorites: () => void
}

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

export const WeekCalendar = forwardRef<WeekCalendarRef, WeekCalendarProps>(function WeekCalendar(
  { calendarData, monday, sourceItem, onSelect, onEdit, loading, error, favorites, onOpenFavorites },
  ref,
) {
  const scrollRef = useRef<HTMLDivElement>(null)
  useImperativeHandle(ref, () => ({
    scrollToRight: () => scrollRef.current?.scrollTo({ left: scrollRef.current.scrollWidth, behavior: 'smooth' }),
  }))

  if (error) {
    return <div className="rounded-md border border-danger/40 bg-red-50 p-3 text-sm text-danger">{error}</div>
  }
  if (loading) {
    return <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground"><span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />加载工时数据...</div>
  }

  const emptyFavorites = Array.isArray(favorites) && favorites.length === 0

  return (
    <div className="space-y-3">
      {emptyFavorites && (
        <div className="flex flex-wrap items-center gap-3 rounded-[10px] border border-dashed border-brand-200 bg-white px-5 py-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-brand-50 text-xl text-brand-500">
            <Star className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="mb-0.5 text-sm font-semibold">还没有关注的空间</div>
            <div className="text-xs text-muted-foreground">
              日历需要知道从哪些空间读取工时。
              <button type="button" onClick={onOpenFavorites} className="text-brand-600 hover:underline">点此添加关注空间</button>。
            </div>
          </div>
          <Button variant="outline" size="sm" className="border-brand-500 text-brand-600" onClick={onOpenFavorites}>
            ＋ 添加关注空间
          </Button>
        </div>
      )}
      <div ref={scrollRef} className="flex gap-3 overflow-x-auto pb-2">
        {WEEKDAYS.map((label, i) => {
          const date = addDays(monday, i)
          const dateStr = format(date, 'yyyy-MM-dd')
          const items = calendarData[dateStr] || []
          const rawTotal = items.reduce((sum, it) => sum + (Number(it.time) || 0), 0)
          const total = Number.isInteger(rawTotal) ? rawTotal : Number(rawTotal.toFixed(1))
          return (
            <div
              key={dateStr}
              className="min-w-[calc((100%-48px)/5)] w-[calc((100%-48px)/5)] shrink-0 rounded-lg border border-[#f0f0f0] bg-white"
            >
              <div className="flex items-center justify-between gap-2 border-b border-[#f0f0f0] px-2.5 py-2">
                <span className="truncate text-[13px] text-[rgba(0,0,0,0.88)]">{label} {dateStr}</span>
                <span className={cn('shrink-0 rounded px-1.5 py-0.5 text-[11px] font-medium', total > 0 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500')}>
                  {total}小时
                </span>
              </div>
              <div className="max-h-[220px] space-y-2 overflow-y-auto p-2">
                {items.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-6 text-muted-foreground">
                    <Inbox className="mb-1 h-7 w-7 opacity-40" />
                    <span className="text-[11px]">无工时记录</span>
                  </div>
                ) : (
                  items.map((item, idx) => {
                    const selected = sourceItem?.object_id === item.object_id
                    return (
                      <div
                        key={item.object_id || idx}
                        role="button"
                        tabIndex={0}
                        onClick={() => onSelect(item)}
                        onKeyDown={(e) => {
                          if (e.target !== e.currentTarget) return
                          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(item) }
                        }}
                        className={cn(
                          'group cursor-pointer rounded-md bg-[#e6f4ff] px-2.5 py-2 text-xs transition-colors hover:bg-[#bae0ff]',
                          selected && 'border border-blue-500 bg-[#bae0ff] ring-1 ring-inset ring-blue-500',
                        )}
                      >
                        <div className="flex items-start gap-1">
                          <div className="min-w-0 flex-1">
                            <div className="leading-snug"><strong className="font-semibold text-danger">{item.time}h</strong> {item.name}</div>
                            <div className="mt-0.5 truncate text-[11px] text-muted-foreground">迭代: {item.sprint || item.sprint_id || '-'}</div>
                          </div>
                          <button
                            type="button"
                            aria-label="编辑"
                            onClick={(e) => { e.stopPropagation(); onEdit(item) }}
                            onKeyDown={(e) => e.stopPropagation()}
                            className="shrink-0 text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
})
