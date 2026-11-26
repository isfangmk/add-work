const COOKIE_KEY = 'savedCookie';
const EXPIRY_KEY = 'cookieExpiry';
const WELCOME_HIDE_KEY = 'welcomePromoHidden';
const YEAR_MS = 365 * 24 * 60 * 60 * 1000;

export type LogLineType = 'success' | 'error' | 'info' | 'default';
export interface ClassifiedLogLine {
  message: string;
  type: LogLineType;
}

export function saveCookie(cookie: string): void {
  if (cookie.trim()) {
    localStorage.setItem(COOKIE_KEY, cookie);
    localStorage.setItem(EXPIRY_KEY, String(Date.now() + YEAR_MS));
  } else {
    localStorage.removeItem(COOKIE_KEY);
    localStorage.removeItem(EXPIRY_KEY);
  }
}

export function loadCookie(): string {
  const cookie = localStorage.getItem(COOKIE_KEY);
  const expiry = localStorage.getItem(EXPIRY_KEY);
  if (cookie && expiry && Date.now() < Number(expiry)) return cookie;
  localStorage.removeItem(COOKIE_KEY);
  localStorage.removeItem(EXPIRY_KEY);
  return '';
}

const RECENT_SEARCH_PREFIX = 'add-work:recent-requirement-search:';
const RECENT_SEARCH_MAX = 3;

function recentSearchKey(username?: string): string {
  return `${RECENT_SEARCH_PREFIX}${username?.trim() || 'default'}`;
}

export function loadRecentSearches(username?: string): string[] {
  try {
    const raw = localStorage.getItem(recentSearchKey(username));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string').slice(0, RECENT_SEARCH_MAX) : [];
  } catch {
    return [];
  }
}

/** 记录一次搜索：去重、最近优先，最多保留 3 条。 */
export function rememberSearch(username: string | undefined, keyword: string): string[] {
  const clean = keyword.trim();
  if (!clean) return loadRecentSearches(username);
  const next = [clean, ...loadRecentSearches(username).filter((k) => k !== clean)].slice(0, RECENT_SEARCH_MAX);
  try {
    localStorage.setItem(recentSearchKey(username), JSON.stringify(next));
  } catch {
    // localStorage 不可用时仅保留内存结果
  }
  return next;
}

export function forgetSearch(username: string | undefined, keyword: string): string[] {
  const next = loadRecentSearches(username).filter((k) => k !== keyword);
  try {
    localStorage.setItem(recentSearchKey(username), JSON.stringify(next));
  } catch {
    // 忽略存储失败
  }
  return next;
}

export function shouldShowWelcomePromo(): boolean {
  return localStorage.getItem(WELCOME_HIDE_KEY) !== '1';
}

export function hideWelcomePromo(): void {
  localStorage.setItem(WELCOME_HIDE_KEY, '1');
}

export function hasValidDays(data: unknown): boolean {
  if (!data || typeof data !== 'object') return false;
  return Object.values(data).some((day) => Array.isArray(day) && day.length > 0);
}

export function collectFilledDates(data?: Record<string, unknown>): Set<string> {
  const set = new Set<string>();
  Object.entries(data || {}).forEach(([date, items]) => {
    if (Array.isArray(items) && items.length > 0) set.add(date);
  });
  return set;
}

export function classifyLogLine(line: string): ClassifiedLogLine {
  if (line.startsWith('✅')) return { message: line, type: 'success' };
  if (line.startsWith('❌')) return { message: line, type: 'error' };
  if (line.startsWith('📅') || line.startsWith('===') || line.startsWith('🎉')) {
    return { message: line, type: 'info' };
  }
  return { message: line, type: 'default' };
}
