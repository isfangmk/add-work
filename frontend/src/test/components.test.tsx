import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CookiePanel } from '@/components/CookiePanel'
import { Button } from '@/components/ui/button'

describe('CookiePanel', () => {
  it('cookie 为空时展示输入框并支持输入', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<CookiePanel cookie="" username={null} onChange={onChange} />)
    const input = screen.getByPlaceholderText(/PRE-GW-SESSION/)
    await user.type(input, 'abc')
    expect(onChange).toHaveBeenCalled()
  })

  it('输入过程中不会因为 filled 变化而折叠 textarea', async () => {
    const user = userEvent.setup()
    function Stateful() {
      const [cookie, setCookie] = useState('')
      return <CookiePanel cookie={cookie} username={null} onChange={setCookie} />
    }
    render(<Stateful />)
    const input = screen.getByPlaceholderText(/PRE-GW-SESSION/)
    await user.type(input, 'abc')
    // 仍在输入态，textarea 不应卸载
    expect(screen.getByPlaceholderText(/PRE-GW-SESSION/)).toHaveValue('abc')
  })

  it('cookie 已填写时展示状态徽标与用户名', () => {
    render(<CookiePanel cookie="valid-cookie" username="fang" onChange={vi.fn()} />)
    expect(screen.getByText(/Cookie 已填写/)).toBeInTheDocument()
    expect(screen.getByText(/当前用户：fang/)).toBeInTheDocument()
  })

  it('切换展开/收起', async () => {
    const user = userEvent.setup()
    render(<CookiePanel cookie="valid-cookie" username="fang" onChange={vi.fn()} />)
    expect(screen.queryByPlaceholderText(/PRE-GW-SESSION/)).not.toBeInTheDocument()
    await user.click(screen.getByText(/展开编辑/))
    expect(screen.getByPlaceholderText(/PRE-GW-SESSION/)).toBeInTheDocument()
  })
})

describe('Button', () => {
  it('loading 时禁用并显示加载态', () => {
    render(<Button loading>提交</Button>)
    const btn = screen.getByRole('button', { name: /提交/ })
    expect(btn).toBeDisabled()
  })

  it('variant 与 size 正确渲染', () => {
    render(<Button variant="destructive" size="icon" aria-label="删除">×</Button>)
    expect(screen.getByRole('button', { name: '删除' })).toHaveClass('bg-destructive')
  })
})
