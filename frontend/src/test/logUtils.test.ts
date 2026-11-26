import { describe, it, expect } from 'vitest'
import { classifyLogLine } from '@/lib/logUtils'

describe('classifyLogLine', () => {
  it('✅ 开头归类为 success', () => {
    expect(classifyLogLine('✅ 成功')).toEqual({ message: '✅ 成功', type: 'success' })
  })

  it('❌ 开头归类为 error', () => {
    expect(classifyLogLine('❌ 失败')).toEqual({ message: '❌ 失败', type: 'error' })
  })

  it('📅 / === / 🎉 开头归类为 info', () => {
    expect(classifyLogLine('📅 日期').type).toBe('info')
    expect(classifyLogLine('=== 分割 ===').type).toBe('info')
    expect(classifyLogLine('🎉 完成').type).toBe('info')
  })

  it('其他内容归类为 default', () => {
    expect(classifyLogLine('普通日志')).toEqual({ message: '普通日志', type: 'default' })
  })

  it('前导换行不影响分类，且保留原始文本', () => {
    expect(classifyLogLine('\n=== 处理第1/2个事项 ===')).toEqual({
      message: '\n=== 处理第1/2个事项 ===', type: 'info',
    })
  })
})
