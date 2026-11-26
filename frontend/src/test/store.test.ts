import { describe, it, expect, beforeEach } from 'vitest'
import { useAppStore } from '@/stores/useAppStore'

describe('useAppStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAppStore.setState({
      cookie: '',
      username: null,
      gitEmail: null,
      weekOffset: 0,
      editOpen: false,
      favoriteOpen: false,
      feedbackOpen: false,
      welcomeOpen: true,
    })
  })

  it('setCookie 持久化 cookie 并重置用户', () => {
    useAppStore.getState().setUser('fang', 'f@x.com')
    useAppStore.getState().setCookie('COOKIE')
    const state = useAppStore.getState()
    expect(state.cookie).toBe('COOKIE')
    expect(state.username).toBeNull()
    expect(localStorage.getItem('savedCookie')).toBe('COOKIE')
  })

  it('清空 cookie 时移除本地存储', () => {
    useAppStore.getState().setCookie('COOKIE')
    useAppStore.getState().setCookie('')
    expect(localStorage.getItem('savedCookie')).toBeNull()
  })

  it('setUser / setWeekOffset / 弹窗状态', () => {
    const s = useAppStore.getState()
    s.setUser('fang', 'f@x.com')
    s.setWeekOffset(-1)
    s.setEditOpen(true)
    const next = useAppStore.getState()
    expect(next.username).toBe('fang')
    expect(next.gitEmail).toBe('f@x.com')
    expect(next.weekOffset).toBe(-1)
    expect(next.editOpen).toBe(true)
  })

  it('setWelcomeOpen 仅关闭弹窗，不写入本地标记', () => {
    useAppStore.getState().setWelcomeOpen(false)
    expect(localStorage.getItem('welcomePromoHidden')).toBeNull()
    expect(useAppStore.getState().welcomeOpen).toBe(false)
  })

  it('hideWelcomePromo 持久化隐藏标记', () => {
    useAppStore.getState().hideWelcomePromo()
    expect(localStorage.getItem('welcomePromoHidden')).toBe('1')
    expect(useAppStore.getState().welcomeOpen).toBe(false)
  })
})
