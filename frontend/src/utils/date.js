export function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** @returns {{ monday: Date, sunday: Date, weekLabel: string }} */
export function getWeekRange(offset = 0) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const monday = new Date(today);
  const dow = today.getDay() || 7;
  monday.setDate(today.getDate() - (dow - 1) + offset * 7);

  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  let weekLabel = '本周';
  if (offset < 0) weekLabel = `${Math.abs(offset)}周前`;
  if (offset > 0) weekLabel = `${offset}周后`;

  return { monday, sunday, weekLabel };
}

export function isWeekend(dateStr) {
  const day = new Date(dateStr).getDay();
  return day === 0 || day === 6;
}

export function isInCurrentWeek(dateStr) {
  const d = new Date(dateStr);
  const { monday, sunday } = getWeekRange(0);
  return d >= monday && d <= sunday;
}
