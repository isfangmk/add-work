import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const COOKIE_KEY = 'savedCookie'
const YEAR_MS = 365 * 24 * 60 * 60 * 1000

function loadCookie(): string {
  const cookie = localStorage.getItem(COOKIE_KEY)
  const expiry = localStorage.getItem('cookieExpiry')
  if (cookie && expiry && Date.now() < Number(expiry)) return cookie
  localStorage.removeItem(COOKIE_KEY)
  localStorage.removeItem('cookieExpiry')
  return ''
}

interface AppState {
  cookie: string
  username: string | null
  gitEmail: string | null
  weekOffset: number
  editOpen: boolean
  favoriteOpen: boolean
  feedbackOpen: boolean
  welcomeOpen: boolean
  setCookie: (cookie: string) => void
  setUser: (username: string | null, gitEmail: string | null) => void
  setWeekOffset: (offset: number) => void
  setEditOpen: (open: boolean) => void
  setFavoriteOpen: (open: boolean) => void
  setFeedbackOpen: (open: boolean) => void
  setWelcomeOpen: (open: boolean) => void
  hideWelcomePromo: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      cookie: loadCookie(),
      username: null,
      gitEmail: null,
      weekOffset: 0,
      editOpen: false,
      favoriteOpen: false,
      feedbackOpen: false,
      welcomeOpen: !localStorage.getItem('welcomePromoHidden'),
      setCookie: (cookie) => {
        if (get().cookie === cookie) return
        if (cookie.trim()) {
          localStorage.setItem(COOKIE_KEY, cookie)
          localStorage.setItem('cookieExpiry', String(Date.now() + YEAR_MS))
        } else {
          localStorage.removeItem(COOKIE_KEY)
          localStorage.removeItem('cookieExpiry')
        }
        set({ cookie, username: null, gitEmail: null })
      },
      setUser: (username, gitEmail) => set({ username, gitEmail }),
      setWeekOffset: (weekOffset) => set({ weekOffset }),
      setEditOpen: (editOpen) => set({ editOpen }),
      setFavoriteOpen: (favoriteOpen) => set({ favoriteOpen }),
      setFeedbackOpen: (feedbackOpen) => set({ feedbackOpen }),
      setWelcomeOpen: (welcomeOpen) => set({ welcomeOpen }),
      hideWelcomePromo: () => {
        localStorage.setItem('welcomePromoHidden', '1')
        set({ welcomeOpen: false })
      },
    }),
    {
      name: 'add-work-app',
      // 只持久化 weekOffset；cookie 由 savedCookie + 过期时间独立管理
      partialize: (s) => ({ weekOffset: s.weekOffset }),
      // 只恢复 weekOffset；cookie / 用户态以运行时为准
      merge: (persisted, current) => ({
        ...current,
        weekOffset: Number((persisted as { weekOffset?: number } | undefined)?.weekOffset) || 0,
        cookie: loadCookie(),
        username: null,
        gitEmail: null,
      }),
    },
  ),
)
