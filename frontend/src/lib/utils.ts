import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, startOfWeek, endOfWeek, addWeeks, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** YYYY-MM-DD */
export function formatDate(date: Date): string {
  return format(date, 'yyyy-MM-dd')
}

export function parseDate(value: string): Date {
  return parseISO(value)
}

export interface WeekRange {
  monday: Date
  sunday: Date
  weekLabel: string
}

export function getWeekRange(offset = 0): WeekRange {
  const now = new Date()
  const target = addWeeks(now, offset)
  const monday = startOfWeek(target, { weekStartsOn: 1 })
  const sunday = endOfWeek(target, { weekStartsOn: 1 })

  let weekLabel = '本周'
  if (offset < 0) weekLabel = `${Math.abs(offset)}周前`
  if (offset > 0) weekLabel = `${offset}周后`

  return { monday, sunday, weekLabel }
}

export function isWeekend(dateStr: string): boolean {
  const day = parseDate(dateStr).getDay()
  return day === 0 || day === 6
}

export function isInCurrentWeek(dateStr: string): boolean {
  const d = parseDate(dateStr)
  const { monday, sunday } = getWeekRange(0)
  return d >= monday && d <= sunday
}

export function formatWeekday(dateStr: string): string {
  return format(parseDate(dateStr), 'EEEE', { locale: zhCN })
}

export function formatMonthDay(date: Date): string {
  return format(date, 'M月d日', { locale: zhCN })
}
