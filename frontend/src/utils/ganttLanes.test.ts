import { describe, expect, it } from 'vitest'
import dayjs from 'dayjs'
import type { GanttBlock } from '@/api'
import { layoutRowTrack } from './ganttLanes'

function block(id: number, start: string, end: string): GanttBlock {
  return {
    task_id: id,
    title: `T${id}`,
    user_id: 1,
    user_name: 'u',
    user_avatar: '',
    start_date: start,
    end_date: end,
    status: 'todo',
    progress: 0,
    urgent: false,
    dependencies: [],
  }
}

describe('layoutRowTrack', () => {
  const rangeStart = dayjs('2026-05-26')
  const rangeEnd = dayjs('2026-06-01')

  it('assigns separate lanes for overlapping tasks', () => {
    const layout = layoutRowTrack(
      [block(1, '2026-05-26', '2026-05-28'), block(2, '2026-05-27', '2026-05-30')],
      rangeStart,
      rangeEnd,
      7,
    )
    expect(layout.laneCount).toBe(2)
    expect(layout.bars[0].lane).not.toBe(layout.bars[1].lane)
    expect(layout.rowHeight).toBeGreaterThan(52)
  })

  it('shares one lane when tasks do not overlap', () => {
    const layout = layoutRowTrack(
      [block(1, '2026-05-26', '2026-05-27'), block(2, '2026-05-29', '2026-05-30')],
      rangeStart,
      rangeEnd,
      7,
    )
    expect(layout.laneCount).toBe(1)
    expect(layout.bars.every((b) => b.lane === 0)).toBe(true)
  })

  it('clips task ending after window to the last visible day only', () => {
    const layout = layoutRowTrack(
      [block(1, '2026-05-31', '2026-06-03')],
      dayjs('2026-05-25'),
      dayjs('2026-05-31'),
      7,
    )
    expect(layout.bars).toHaveLength(1)
    expect(layout.bars[0].geometry.spanDays).toBe(1)
    expect(layout.bars[0].geometry.left).toBe(`${(6 / 7) * 100}%`)
    expect(layout.bars[0].geometry.right).toBe('0%')
  })
})
