/** Local YYYY-MM-DD string (avoids the UTC drift of toISOString). */
export function toDateInput(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

/**
 * Parse a YYYY-MM-DD (or ISO) string into a local Date, so a date stored as
 * "2026-08-23" is read as the same calendar day instead of being shifted by
 * the timezone offset.
 */
export function parseLocalDate(value: string): Date {
  const parts = value.slice(0, 10).split('-')
  const y = Number(parts[0])
  const m = Number(parts[1] ?? 1)
  const d = Number(parts[2] ?? 1)
  return new Date(y, m - 1, d)
}

export const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
] as const

export function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

export function formatDate(d: Date, mode: 'day' | 'week' | 'month' | 'year'): string {
  if (mode === 'day') {
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  }
  if (mode === 'week') {
    const start = new Date(d)
    start.setDate(start.getDate() - start.getDay())
    return `Week of ${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
  }
  if (mode === 'month') {
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
  }
  return String(d.getFullYear())
}

export function stepDate(d: Date, mode: 'day' | 'week' | 'month' | 'year', direction: number): Date {
  const next = new Date(d)
  if (mode === 'day') next.setDate(next.getDate() + direction)
  else if (mode === 'week') next.setDate(next.getDate() + 7 * direction)
  else if (mode === 'month') next.setMonth(next.getMonth() + direction)
  else next.setFullYear(next.getFullYear() + direction)
  return next
}
