import dayjs from 'dayjs'
import type { GanttBlock } from '@/api'

export const LANE_HEIGHT = 32
export const LANE_GAP = 4
export const ROW_PAD_Y = 8
export const ROW_MIN_HEIGHT = 52

export interface BarGeometry {
  left: string
  right: string
  spanDays: number
}

/** Parse API calendar dates without timezone drift (YYYY-MM-DD). */
export function parseTaskDate(iso: string): dayjs.Dayjs {
  const day = iso.slice(0, 10)
  return dayjs(day, 'YYYY-MM-DD', true)
}

export interface PlacedGanttBar {
  block: GanttBlock
  lane: number
  geometry: BarGeometry
  top: string
  height: string
}

export interface RowTrackLayout {
  bars: PlacedGanttBar[]
  laneCount: number
  rowHeight: number
}

function clipIndices(
  block: GanttBlock,
  rangeStart: dayjs.Dayjs,
  rangeEnd: dayjs.Dayjs,
): { startIdx: number; endIdx: number } | null {
  if (!block.start_date || !block.end_date) return null
  const tStart = parseTaskDate(block.start_date)
  const tEnd = parseTaskDate(block.end_date)
  if (!tStart.isValid() || !tEnd.isValid()) return null
  if (tEnd.isBefore(rangeStart, 'day') || tStart.isAfter(rangeEnd, 'day')) return null

  const clipStart = tStart.isBefore(rangeStart) ? rangeStart : tStart
  const clipEnd = tEnd.isAfter(rangeEnd) ? rangeEnd : tEnd
  return {
    startIdx: clipStart.diff(rangeStart, 'day'),
    endIdx: clipEnd.diff(rangeStart, 'day'),
  }
}

function barGeometry(startIdx: number, endIdx: number, dayCount: number): BarGeometry {
  const spanDays = endIdx - startIdx + 1
  return {
    spanDays,
    left: `${(startIdx / dayCount) * 100}%`,
    right: `${((dayCount - endIdx - 1) / dayCount) * 100}%`,
  }
}

/** Greedy lane packing: overlapping inclusive date ranges use separate tracks. */
function assignLanes(
  items: { block: GanttBlock; startIdx: number; endIdx: number }[],
): { block: GanttBlock; startIdx: number; endIdx: number; lane: number }[] {
  const sorted = [...items].sort(
    (a, b) => a.startIdx - b.startIdx || b.endIdx - a.endIdx - (a.endIdx - a.startIdx),
  )
  const laneExclusiveEnds: number[] = []

  return sorted.map((item) => {
    const exclusiveEnd = item.endIdx + 1
    let lane = laneExclusiveEnds.findIndex((end) => end <= item.startIdx)
    if (lane === -1) {
      lane = laneExclusiveEnds.length
      laneExclusiveEnds.push(exclusiveEnd)
    } else {
      laneExclusiveEnds[lane] = exclusiveEnd
    }
    return { ...item, lane }
  })
}

export function layoutRowTrack(
  blocks: GanttBlock[],
  rangeStart: dayjs.Dayjs,
  rangeEnd: dayjs.Dayjs,
  dayCount: number,
): RowTrackLayout {
  const clipped = blocks
    .map((block) => {
      const idx = clipIndices(block, rangeStart, rangeEnd)
      return idx ? { block, ...idx } : null
    })
    .filter((x): x is { block: GanttBlock; startIdx: number; endIdx: number } => x != null)

  const placed = assignLanes(clipped)
  const laneCount = Math.max(1, ...placed.map((p) => p.lane + 1))
  const rowHeight = Math.max(
    ROW_MIN_HEIGHT,
    ROW_PAD_Y * 2 + laneCount * LANE_HEIGHT + (laneCount - 1) * LANE_GAP,
  )

  const bars: PlacedGanttBar[] = placed.map((p) => {
    const geometry = barGeometry(p.startIdx, p.endIdx, dayCount)
    const topPx = ROW_PAD_Y + p.lane * (LANE_HEIGHT + LANE_GAP)
    return {
      block: p.block,
      lane: p.lane,
      geometry,
      top: `${topPx}px`,
      height: `${LANE_HEIGHT}px`,
    }
  })

  return { bars, laneCount, rowHeight }
}
