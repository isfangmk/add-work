import { describe, it, expect } from 'vitest'
import {
  cn,
  formatDate,
  parseDate,
  getWeekRange,
  isWeekend,
  isInCurrentWeek,
  formatWeekday,
  formatMonthDay,
} from '@/lib/utils'

describe('cn', () => {
  it('合并类名并移除冲突类', () => {
    expect(cn('px-2', 'px-4', 'text-sm')).toBe('px-4 text-sm')
  })
})

describe('日期工具', () => {
  it('formatDate 输出 YYYY-MM-DD', () => {
    expect(formatDate(new Date(2026, 10, 24))).toBe('2026-11-24')
  })

  it('parseDate 解析 ISO 日期字符串', () => {
    expect(formatDate(parseDate('2026-11-24'))).toBe('2026-11-24')
  })

  it('getWeekRange 周一到周日，偏移标签正确', () => {
    const current = getWeekRange(0)
    expect(current.monday.getDay()).toBe(1)
    expect(current.sunday.getDay()).toBe(0)
    expect(current.weekLabel).toBe('本周')
    expect(getWeekRange(-2).weekLabel).toBe('2周前')
    expect(getWeekRange(3).weekLabel).toBe('3周后')
  })

  it('isWeekend 识别周末', () => {
    expect(isWeekend('2026-11-28')).toBe(true)
    expect(isWeekend('2026-11-29')).toBe(true)
    expect(isWeekend('2026-11-24')).toBe(false)
  })

  it('isInCurrentWeek 判断日期是否在本周', () => {
    const { monday } = getWeekRange(0)
    expect(isInCurrentWeek(formatDate(monday))).toBe(true)
    expect(isInCurrentWeek('2020-01-01')).toBe(false)
  })

  it('formatWeekday / formatMonthDay 使用中文', () => {
    expect(formatWeekday('2026-11-24')).toBe('星期二')
    expect(formatMonthDay(new Date(2026, 10, 24))).toBe('11月24日')
  })
})
