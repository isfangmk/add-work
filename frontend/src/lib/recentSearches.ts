const PREFIX = 'add-work:recent-requirement-search:'
const MAX = 3

function key(username?: string | null) {
  return `${PREFIX}${username?.trim() || 'default'}`
}

export function loadRecentSearches(username?: string | null): string[] {
  try {
    const raw = localStorage.getItem(key(username))
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed)
      ? parsed.filter((x): x is string => typeof x === 'string').slice(0, MAX)
      : []
  } catch {
    return []
  }
}

/** 记录一次搜索：去重、最近优先，最多 3 条 */
export function rememberSearch(username: string | null | undefined, keyword: string): string[] {
  const clean = keyword.trim()
  if (!clean) return loadRecentSearches(username)
  const next = [clean, ...loadRecentSearches(username).filter((k) => k !== clean)].slice(0, MAX)
  try {
    localStorage.setItem(key(username), JSON.stringify(next))
  } catch {
    // localStorage 不可用时仅保留内存结果
  }
  return next
}

export function forgetSearch(username: string | null | undefined, keyword: string): string[] {
  const clean = keyword.trim()
  const next = loadRecentSearches(username).filter((k) => k !== clean)
  try {
    localStorage.setItem(key(username), JSON.stringify(next))
  } catch {
    // 忽略存储失败
  }
  return next
}
