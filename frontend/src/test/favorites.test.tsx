import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FavoriteSpacesModal } from '@/components/FavoriteSpacesModal'
import * as queries from '@/hooks/queries'

vi.mock('@/hooks/queries', () => ({
  useWorkspaces: vi.fn(),
}))

const WORKSPACES = [
  { workspace_name: 'WS1', workspace_key: '1', workspace_id: '1' },
  { workspace_name: 'WS2', workspace_key: '2', workspace_id: '2' },
]

describe('FavoriteSpacesModal', () => {
  beforeEach(() => {
    vi.mocked(queries.useWorkspaces).mockReturnValue({ data: WORKSPACES } as never)
  })

  it('打开时以最新 favorites 初始化选中态', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(true)
    const { rerender } = render(
      <FavoriteSpacesModal open={false} cookie="C" favorites={[]} onClose={vi.fn()} onSave={onSave} />,
    )
    // 组件挂载后 favorites 异步到达
    rerender(
      <FavoriteSpacesModal
        open
        cookie="C"
        favorites={[{ workspace_name: 'WS1', workspace_key: '1' }]}
        onClose={vi.fn()}
        onSave={onSave}
      />,
    )
    expect(screen.getByRole('button', { name: /保存（1）/ })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /保存（1）/ }))
    expect(onSave).toHaveBeenCalledWith(
      expect.arrayContaining([expect.objectContaining({ workspace_name: 'WS1' })]),
    )
    expect(onSave.mock.calls[0][0]).toHaveLength(1)
  })

  it('保存失败时不关闭弹窗', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const onSave = vi.fn().mockResolvedValue(false)
    render(
      <FavoriteSpacesModal open cookie="C" favorites={[]} onClose={onClose} onSave={onSave} />,
    )
    await user.click(screen.getByRole('button', { name: /保存（0）/ }))
    expect(onSave).toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled()
  })

  it('保存成功时关闭弹窗', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const onSave = vi.fn().mockResolvedValue(true)
    render(
      <FavoriteSpacesModal open cookie="C" favorites={[]} onClose={onClose} onSave={onSave} />,
    )
    await user.click(screen.getByRole('button', { name: /保存（0）/ }))
    await vi.waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
