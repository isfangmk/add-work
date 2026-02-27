const COOKIE_KEY = 'savedCookie';
const EXPIRY_KEY = 'cookieExpiry';
const YEAR_MS = 365 * 24 * 60 * 60 * 1000;

export function saveCookie(cookie) {
  if (cookie.trim()) {
    localStorage.setItem(COOKIE_KEY, cookie);
    localStorage.setItem(EXPIRY_KEY, String(Date.now() + YEAR_MS));
  } else {
    localStorage.removeItem(COOKIE_KEY);
    localStorage.removeItem(EXPIRY_KEY);
  }
}

export function loadCookie() {
  const cookie = localStorage.getItem(COOKIE_KEY);
  const expiry = localStorage.getItem(EXPIRY_KEY);
  if (cookie && expiry && Date.now() < Number(expiry)) return cookie;
  localStorage.removeItem(COOKIE_KEY);
  localStorage.removeItem(EXPIRY_KEY);
  return '';
}

export function hasValidDays(data) {
  if (!data || typeof data !== 'object') return false;
  return Object.values(data).some((day) => Array.isArray(day) && day.length > 0);
}

export function collectFilledDates(data) {
  const set = new Set();
  Object.entries(data || {}).forEach(([date, items]) => {
    if (Array.isArray(items) && items.length > 0) set.add(date);
  });
  return set;
}

export function classifyLogLine(line) {
  if (line.startsWith('✅')) return { message: line, type: 'success' };
  if (line.startsWith('❌')) return { message: line, type: 'error' };
  if (line.startsWith('📅') || line.startsWith('===') || line.startsWith('🎉')) {
    return { message: line, type: 'info' };
  }
  return { message: line, type: 'default' };
}
