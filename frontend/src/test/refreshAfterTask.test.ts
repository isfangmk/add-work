import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const appSource = readFileSync(resolve(here, '../App.tsx'), 'utf-8')

describe('任务完成后的日历刷新', () => {
  it('不再使用 useWorkItems 的手动 refetch（避免与 invalidateQueries 重复请求）', () => {
    expect(appSource).not.toContain('refetch: refetchCalendar')
    expect(appSource).not.toContain('refetchCalendar()')
  })

  it('refreshAfterTask 仅通过 invalidateQueries 或切周触发一次刷新', () => {
    const fn = appSource.slice(
      appSource.indexOf('const refreshAfterTask'),
      appSource.indexOf('}, [weekOffset'),
    )
    // 一次调用只走其中一条分支：切周 setWeekOffset，否则 invalidateQueries
    expect(fn).toContain('setWeekOffset(0)')
    expect(fn).toContain('invalidateQueries')
    expect(fn).not.toContain('refetchCalendar')
  })
})
