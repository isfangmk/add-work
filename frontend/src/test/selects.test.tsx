import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SprintSelect } from '@/components/SprintSelect'
import { RequirementSelect } from '@/components/RequirementSelect'
import * as queries from '@/hooks/queries'

vi.mock('@/hooks/queries', () => ({
  useSprints: vi.fn(),
  useRequirements: vi.fn(),
}))

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>
}

describe('SprintSelect', () => {
  beforeEach(() => {
    vi.mocked(queries.useSprints).mockReturnValue({
      data: [
        { object_id: 'S1', name: '迭代一', workspace_name: 'WS' },
        { object_id: 'S2', name: 'ONE4.0.5.0', workspace_name: 'WS2' },
      ],
      isFetching: false,
    } as never)
  })

  it('默认展示当前空间迭代，勾选框存在且位于搜索框下方', async () => {
    const user = userEvent.setup()
    render(wrap(<SprintSelect value="" onChange={vi.fn()} cookie="C" workspaceName="WS" />))
    await user.click(screen.getByRole('combobox'))
    const label = screen.getByText('只显示当前空间的迭代')
    expect(label).toBeInTheDocument()
    expect(screen.getByText('迭代一')).toBeInTheDocument()
    const input = screen.getByPlaceholderText('搜索迭代…')
    expect(input.compareDocumentPosition(label) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('勾选框可切换，切换后仍展示选项', async () => {
    const user = userEvent.setup()
    render(wrap(<SprintSelect value="" onChange={vi.fn()} cookie="C" workspaceName="WS" />))
    await user.click(screen.getByRole('combobox'))
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveAttribute('data-state', 'checked')
    await user.click(checkbox)
    await waitFor(() => expect(screen.getByRole('checkbox')).toHaveAttribute('data-state', 'unchecked'))
  })

  it('点击选项触发 onChange', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(wrap(<SprintSelect value="" onChange={onChange} cookie="C" workspaceName="WS" />))
    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByText('迭代一'))
    expect(onChange).toHaveBeenCalledWith('S1', '迭代一')
  })
})

describe('RequirementSelect', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(queries.useRequirements).mockReturnValue({
      data: [
        { id: 'R1', key: '105-1', name: '需求一' },
        { id: 'R2', key: '', name: '需求二' },
      ],
      isFetching: false,
    } as never)
  })

  it('展示历史 chips，点击填入并搜索', async () => {
    const user = userEvent.setup()
    localStorage.setItem('add-work:recent-requirement-search:fang', JSON.stringify(['Titan']))
    render(wrap(<RequirementSelect value="" onChange={vi.fn()} cookie="C" username="fang" />))
    await user.click(screen.getByRole('combobox'))
    expect(screen.getByText('最近')).toBeInTheDocument()
    expect(screen.getByTitle('Titan')).toBeInTheDocument()
    // 最近搜索位于搜索框下方
    const input = screen.getByPlaceholderText('输入关键字后回车搜索…')
    expect(input.compareDocumentPosition(screen.getByText('最近')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('回车搜索写入历史并展示', async () => {
    const user = userEvent.setup()
    render(wrap(<RequirementSelect value="" onChange={vi.fn()} cookie="C" username="fang" />))
    await user.click(screen.getByRole('combobox'))
    const input = screen.getByPlaceholderText('输入关键字后回车搜索…')
    await user.type(input, '交付管理{Enter}')
    await waitFor(() => {
      expect(localStorage.getItem('add-work:recent-requirement-search:fang')).toBe('["交付管理"]')
    })
    expect(screen.getByText('最近')).toBeInTheDocument()
  })

  it('历史 chip 可删除', async () => {
    const user = userEvent.setup()
    localStorage.setItem('add-work:recent-requirement-search:fang', JSON.stringify(['Titan']))
    render(wrap(<RequirementSelect value="" onChange={vi.fn()} cookie="C" username="fang" />))
    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByLabelText('删除'))
    await waitFor(() => {
      expect(localStorage.getItem('add-work:recent-requirement-search:fang')).toBe('[]')
    })
  })

  it('关闭后重开清除上次搜索词', async () => {
    const user = userEvent.setup()
    render(wrap(<RequirementSelect value="" onChange={vi.fn()} cookie="C" username="fang" />))
    const trigger = screen.getAllByRole('combobox')[0]
    await user.click(trigger)
    const input = screen.getByPlaceholderText('输入关键字后回车搜索…')
    await user.type(input, '交付')
    expect(input).toHaveValue('交付')
    // 关闭（再次点击 trigger）后重开
    await user.click(trigger)
    await user.click(trigger)
    const reopened = screen.getByPlaceholderText('输入关键字后回车搜索…')
    expect(reopened).toHaveValue('')
  })

  it('选中需求触发 onChange 携带 id 与 name', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(wrap(<RequirementSelect value="" onChange={onChange} cookie="C" username="fang" />))
    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByText(/105-1.*需求一/))
    expect(onChange).toHaveBeenCalledWith('R1', '需求一')
  })
})
