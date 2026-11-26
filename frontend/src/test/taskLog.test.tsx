import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TaskLogPanel } from '@/components/TaskLogPanel'

describe('TaskLogPanel', () => {
  it('空态展示提示文案', () => {
    const { container } = render(<TaskLogPanel taskLog={[]} />)
    expect(screen.getByText(/选择源事项并填写表单后/)).toBeInTheDocument()
    expect(container.firstElementChild).toHaveClass('min-h-[72px]')
  })

  it('有日志时使用固定高度容器并保留原始文本', () => {
    const { container } = render(
      <TaskLogPanel
        taskLog={[{ message: '正在处理...', type: 'info' }]}
      />,
    )
    expect(container.firstElementChild).toHaveClass('h-[280px]')
    expect(screen.getByText('正在处理...')).toBeInTheDocument()
  })

  it('success 与 error 使用对应颜色文本，且不渲染图标', () => {
    const { container } = render(
      <TaskLogPanel
        taskLog={[
          { message: '✅ 成功', type: 'success' },
          { message: '❌ 失败', type: 'error' },
        ]}
      />,
    )
    const lines = container.querySelectorAll('.whitespace-pre-wrap')
    expect(lines).toHaveLength(2)
    expect(lines[0]).toHaveClass('text-[#52c41a]')
    expect(lines[1]).toHaveClass('text-[#ff4d4f]')
    expect(container.querySelector('svg')).toBeNull()
  })

  it('URL 渲染为安全链接', () => {
    render(
      <TaskLogPanel
        taskLog={[{ message: '完成 https://example.com/a', type: 'success' }]}
      />,
    )
    const link = screen.getByRole('link', { name: 'https://example.com/a' })
    expect(link).toHaveAttribute('href', 'https://example.com/a')
    expect(link).toHaveAttribute('target', '_blank')
  })
})
