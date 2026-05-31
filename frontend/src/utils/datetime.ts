import dayjs, { type Dayjs } from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)

/** Parse API timestamps (UTC with Z, or legacy naive UTC). */
export function parseApiDate(value: string | Date | null | undefined): Dayjs {
  if (value == null || value === '') {
    return dayjs.invalid()
  }
  if (value instanceof Date) {
    return dayjs(value)
  }
  const s = String(value).trim()
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s) && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) {
    return dayjs.utc(s)
  }
  return dayjs(s)
}

/** Display in browser local timezone (东八区浏览器即为北京时间). */
export function toLocal(value: string | Date | null | undefined): Dayjs {
  return parseApiDate(value).local()
}

export function formatDateTime(
  value: string | Date | null | undefined,
  pattern = 'YYYY-MM-DD HH:mm',
): string {
  const t = toLocal(value)
  return t.isValid() ? t.format(pattern) : '—'
}

export function formatDate(
  value: string | Date | null | undefined,
  pattern = 'YYYY-MM-DD',
): string {
  return formatDateTime(value, pattern)
}

/**
 * Task DDL / start dates: always bucket by local calendar day (browser TZ).
 * Avoids UTC datetime strings shifting the day (e.g. late-night UTC → previous local day).
 */
export function parseCalendarDate(value: string | Date | null | undefined): Dayjs {
  if (value == null || value === '') {
    return dayjs.invalid()
  }
  if (value instanceof Date) {
    return dayjs(value).startOf('day')
  }
  const s = String(value).trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    return dayjs(s, 'YYYY-MM-DD')
  }
  const t = parseApiDate(value)
  return t.isValid() ? t.local().startOf('day') : t
}

/** YYYY-MM-DD key for calendar cells and filters. */
export function calendarDateKey(value: string | Date | null | undefined): string {
  const t = parseCalendarDate(value)
  return t.isValid() ? t.format('YYYY-MM-DD') : ''
}

/** Start of today in the browser local timezone. */
export function calendarToday(): Dayjs {
  return dayjs().startOf('day')
}

export function relativeTime(value: string | Date | null | undefined): string {
  const t = toLocal(value)
  if (!t.isValid()) return '—'
  const now = dayjs()
  const diffSec = now.diff(t, 'second')
  if (diffSec < 60) return '刚刚'
  const diffMin = now.diff(t, 'minute')
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = now.diff(t, 'hour')
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = now.diff(t, 'day')
  if (diffDay === 1) return '昨天'
  if (diffDay < 7) return `${diffDay} 天前`
  return t.format('YYYY-MM-DD HH:mm')
}
