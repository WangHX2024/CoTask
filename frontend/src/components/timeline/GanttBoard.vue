<template>
  <div
    class="cotask-gantt"
    :style="boardStyle"
    role="grid"
    :aria-rowcount="rows.length + 1"
    :aria-colcount="days.length + 1"
  >
    <div class="cotask-gantt__scroll">
      <div class="cotask-gantt__inner">
        <!-- Header -->
        <div class="cotask-gantt__header" role="row">
          <div class="cotask-gantt__corner" role="columnheader" aria-label="成员" />
          <div class="cotask-gantt__days" role="presentation">
            <div
              v-for="day in days"
              :key="day.key"
              class="cotask-gantt__head-cell"
              role="columnheader"
              :class="{
                'is-today': day.isToday,
                'is-weekend': day.isWeekend,
              }"
            >
              <span class="cotask-gantt__head-wd">{{ day.weekday }}</span>
              <span class="cotask-gantt__head-num">{{ day.num }}</span>
            </div>
          </div>
        </div>

        <!-- Member rows -->
        <div
          v-for="(row, rowIndex) in rows"
          :key="row.user_id"
          class="cotask-gantt__row"
          role="row"
          :class="{ 'is-alt': rowIndex % 2 === 1 }"
        >
          <div class="cotask-gantt__label" role="rowheader">
            <el-avatar :size="28" :src="row.avatar_url || undefined" class="cotask-gantt__avatar">
              {{ (row.name || '?').slice(0, 1) }}
            </el-avatar>
            <span class="cotask-gantt__name" :title="row.name">{{ row.name || '未命名' }}</span>
            <span v-if="row.role === 'leader'" class="cotask-gantt__badge">组长</span>
          </div>

          <div
            class="cotask-gantt__track"
            role="gridcell"
            :style="{ minHeight: `${trackLayout(row).rowHeight}px` }"
          >
            <div class="cotask-gantt__cells" aria-hidden="true">
              <div
                v-for="day in days"
                :key="day.key"
                class="cotask-gantt__cell"
                :class="{
                  'is-today': day.isToday,
                  'is-weekend': day.isWeekend,
                }"
              />
            </div>

            <div
              v-if="todayMarkerLeft != null"
              class="cotask-gantt__today"
              :style="{ left: `${todayMarkerLeft}%` }"
              aria-hidden="true"
            />

            <div
              v-for="placed in trackLayout(row).bars"
              :key="`${row.user_id}-${placed.block.task_id}`"
              class="cotask-gantt__bar-anchor"
              :style="barStyle(placed)"
            >
              <el-tooltip
                placement="top"
                :show-after="250"
                :hide-after="80"
                :enterable="true"
                :show-arrow="false"
                teleported
                popper-class="cotask-gantt-popper"
              >
                <template #content>
                  <div class="gantt-tip">
                    <div class="gantt-tip__path" :title="taskPathFull(placed.block)">
                      <template
                        v-for="(seg, segIdx) in taskPathSegments(placed.block)"
                        :key="segIdx"
                      >
                        <span v-if="segIdx > 0" class="gantt-tip__path-sep">/</span>
                        <span
                          class="gantt-tip__path-seg"
                          :class="{ 'is-path-current': segIdx === taskPathSegments(placed.block).length - 1 }"
                        >{{ seg }}</span>
                      </template>
                    </div>
                    <ul class="gantt-tip__list">
                      <li>
                        <span class="gantt-tip__label">起止</span>
                        <span>{{ barDateRangeFull(placed.block) }}</span>
                      </li>
                      <li>
                        <span class="gantt-tip__label">状态</span>
                        <span
                          class="gantt-tip__status"
                          :class="`gantt-tip__status--${placed.block.status}`"
                        >{{ statusLabel(placed.block.status) }}</span>
                      </li>
                      <li v-if="placed.block.urgent">
                        <span class="gantt-tip__label">提醒</span>
                        <span class="gantt-tip__urgent">紧急截止</span>
                      </li>
                    </ul>
                  </div>
                </template>
                <button
                  type="button"
                  class="cotask-gantt__bar"
                  :class="barClasses(placed)"
                  @click="emit('blockClick', placed.block.task_id)"
                >
                <span class="cotask-gantt__bar-body">
                  <span class="cotask-gantt__dot" aria-hidden="true" />
                  <span class="cotask-gantt__bar-title">{{ barDisplayTitle(placed) }}</span>
                  <span v-if="showBarDates(placed)" class="cotask-gantt__bar-dates">
                    {{ barDateRange(placed.block) }}
                  </span>
                  <span
                    v-if="showBarChip(placed)"
                    class="cotask-gantt__chip"
                    :class="`cotask-gantt__chip--${placed.block.status}`"
                  >{{ statusLabel(placed.block.status) }}</span>
                </span>
                <span class="cotask-gantt__prog" aria-hidden="true">
                  <span
                    class="cotask-gantt__prog-fill"
                    :class="`cotask-gantt__prog-fill--${placed.block.status}`"
                    :style="{ width: `${barPct(placed.block)}%` }"
                  />
                </span>
                </button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElAvatar, ElTooltip } from 'element-plus'
import dayjs from 'dayjs'
import type { GroupRow, GanttBlock } from '@/api'
import { taskBarPercent } from '@/utils/taskProgress'
import { layoutRowTrack, type PlacedGanttBar, type RowTrackLayout } from '@/utils/ganttLanes'

interface Props {
  rows: GroupRow[]
  start: string
  end: string
  view: 'week' | 'month'
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'blockClick', taskId: number): void
}>()

const WEEKDAY_SHORT = ['日', '一', '二', '三', '四', '五', '六'] as const
const LABEL_W = 200
const COL_MIN_WEEK = 56
const COL_MIN_MONTH = 34

const STATUS_LABELS: Record<string, string> = {
  todo: '待办',
  in_progress: '进行中',
  done: '已完成',
  blocked: '已阻塞',
}

interface DayCol {
  key: string
  weekday: string
  num: number
  isToday: boolean
  isWeekend: boolean
}

const rangeStart = computed(() => dayjs(props.start.slice(0, 10), 'YYYY-MM-DD', true).startOf('day'))
const rangeEnd = computed(() => dayjs(props.end.slice(0, 10), 'YYYY-MM-DD', true).startOf('day'))

const days = computed<DayCol[]>(() => {
  const out: DayCol[] = []
  let cur = rangeStart.value
  const end = rangeEnd.value
  const todayKey = dayjs().format('YYYY-MM-DD')
  while (cur.isBefore(end) || cur.isSame(end, 'day')) {
    const key = cur.format('YYYY-MM-DD')
    const dow = cur.day()
    out.push({
      key,
      weekday: viewWeekdayLabel(cur),
      num: cur.date(),
      isToday: key === todayKey,
      isWeekend: dow === 0 || dow === 6,
    })
    cur = cur.add(1, 'day')
  }
  return out
})

const dayCount = computed(() => Math.max(days.value.length, 1))
const colMin = computed(() => (props.view === 'week' ? COL_MIN_WEEK : COL_MIN_MONTH))

const boardStyle = computed(() => ({
  '--gantt-label-w': `${LABEL_W}px`,
  '--gantt-col-min': `${colMin.value}px`,
  '--gantt-track-w': `${dayCount.value * colMin.value}px`,
}))

const layoutCache = computed(() => {
  const map = new Map<number, RowTrackLayout>()
  for (const row of props.rows) {
    map.set(
      row.user_id,
      layoutRowTrack(row.blocks, rangeStart.value, rangeEnd.value, dayCount.value),
    )
  }
  return map
})

function trackLayout(row: GroupRow): RowTrackLayout {
  return layoutCache.value.get(row.user_id) ?? {
    bars: [],
    laneCount: 1,
    rowHeight: 52,
  }
}

function viewWeekdayLabel(d: dayjs.Dayjs): string {
  if (props.view === 'week') {
    return `周${WEEKDAY_SHORT[d.day()]}`
  }
  return WEEKDAY_SHORT[d.day()]
}

function barPct(block: GanttBlock): number {
  return taskBarPercent({ status: block.status, progress: block.progress })
}

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

function formatShortDate(iso: string): string {
  const d = dayjs(iso.slice(0, 10), 'YYYY-MM-DD', true)
  return `${d.month() + 1}/${d.date()}`
}

function barDateRange(block: GanttBlock): string {
  return `${formatShortDate(block.start_date)}–${formatShortDate(block.end_date)}`
}

function formatFullDate(iso: string): string {
  return dayjs(iso.slice(0, 10), 'YYYY-MM-DD', true).format('YYYY年M月D日')
}

function barDateRangeFull(block: GanttBlock): string {
  const s = dayjs(block.start_date.slice(0, 10), 'YYYY-MM-DD', true)
  const e = dayjs(block.end_date.slice(0, 10), 'YYYY-MM-DD', true)
  const endFmt = s.year() === e.year() ? 'M月D日' : 'YYYY年M月D日'
  return `${formatFullDate(block.start_date)} — ${e.format(endFmt)}`
}

function showBarDates(placed: PlacedGanttBar): boolean {
  return placed.geometry.spanDays >= 2 || props.view === 'week'
}

function showBarChip(placed: PlacedGanttBar): boolean {
  return placed.geometry.spanDays >= 2
}

function taskPathSegments(block: GanttBlock): string[] {
  const raw = block.title_path?.trim()
  if (raw) {
    return raw.split(/\s*\/\s*/).filter(Boolean)
  }
  return [block.title || '未命名任务']
}

function taskPathFull(block: GanttBlock): string {
  return taskPathSegments(block).join(' / ')
}

function showBarTitlePath(placed: PlacedGanttBar): boolean {
  const segs = taskPathSegments(placed.block)
  if (segs.length <= 1) return false
  return placed.geometry.spanDays >= 3
    || (props.view === 'week' && placed.geometry.spanDays >= 2)
}

function barDisplayTitle(placed: PlacedGanttBar): string {
  if (showBarTitlePath(placed)) {
    return taskPathFull(placed.block)
  }
  return placed.block.title || '未命名任务'
}

function barClasses(placed: PlacedGanttBar): Record<string, boolean> {
  const b = placed.block
  return {
    [`status-${b.status}`]: true,
    'is-narrow': !showBarChip(placed),
    'is-done': b.status === 'done',
  }
}

function barStyle(placed: PlacedGanttBar): Record<string, string> {
  return {
    left: placed.geometry.left,
    right: placed.geometry.right,
    top: placed.top,
    height: placed.height,
  }
}

const todayMarkerLeft = computed<number | null>(() => {
  const idx = days.value.findIndex((d) => d.isToday)
  if (idx < 0) return null
  return ((idx + 0.5) / dayCount.value) * 100
})
</script>

<style lang="scss" scoped>
.cotask-gantt {
  flex: 1;
  min-height: 420px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-card);
}

.cotask-gantt__scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.cotask-gantt__inner {
  min-width: calc(var(--gantt-label-w) + var(--gantt-track-w));
}

/* ── Header ── */
.cotask-gantt__header {
  display: flex;
  position: sticky;
  top: 0;
  z-index: 4;
  background: var(--bg-soft);
  border-bottom: 1px solid var(--border-color);
}

.cotask-gantt__corner {
  flex: 0 0 var(--gantt-label-w);
  width: var(--gantt-label-w);
  position: sticky;
  left: 0;
  z-index: 5;
  background: var(--bg-soft);
  border-right: 1px solid var(--border-color);
}

.cotask-gantt__days {
  display: flex;
  flex: 1 0 var(--gantt-track-w);
  min-width: var(--gantt-track-w);
}

.cotask-gantt__head-cell {
  flex: 1 0 var(--gantt-col-min);
  min-width: var(--gantt-col-min);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  padding: var(--space-2) var(--space-1);
  border-right: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: var(--fs-xs);
  font-weight: 500;
  line-height: 1.25;

  &:last-child {
    border-right: none;
  }

  &.is-today {
    color: var(--color-primary);
    font-weight: 600;
    background: color-mix(in srgb, var(--color-primary) 8%, var(--bg-soft));
  }

  &.is-weekend:not(.is-today) {
    color: var(--text-tertiary);
    background: color-mix(in srgb, var(--bg-soft) 70%, var(--bg-card));
  }
}

.cotask-gantt__head-wd {
  font-size: var(--fs-xs);
}

.cotask-gantt__head-num {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
}

/* ── Rows ── */
.cotask-gantt__row {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);

  &.is-alt {
    .cotask-gantt__label {
      background: color-mix(in srgb, var(--bg-soft) 65%, var(--bg-card));
    }
    .cotask-gantt__track {
      background: color-mix(in srgb, var(--bg-soft) 40%, var(--bg-card));
    }
  }
}

.cotask-gantt__label {
  flex: 0 0 var(--gantt-label-w);
  width: var(--gantt-label-w);
  align-self: stretch;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0 var(--space-3);
  position: sticky;
  left: 0;
  z-index: 2;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  box-sizing: border-box;
}

.cotask-gantt__avatar {
  flex-shrink: 0;
}

.cotask-gantt__name {
  flex: 1;
  min-width: 0;
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cotask-gantt__badge {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.2;
  padding: 1px 7px;
  border-radius: var(--radius-full);
  background: color-mix(in srgb, var(--color-warning) 14%, transparent);
  color: var(--color-warning);
}

/* ── Track ── */
.cotask-gantt__track {
  position: relative;
  flex: 1 0 var(--gantt-track-w);
  min-width: var(--gantt-track-w);
  background: var(--bg-card);
}

.cotask-gantt__cells {
  position: absolute;
  inset: 0;
  display: flex;
  pointer-events: none;
}

.cotask-gantt__cell {
  flex: 1 0 var(--gantt-col-min);
  min-width: var(--gantt-col-min);
  border-right: 1px solid color-mix(in srgb, var(--border-color) 35%, transparent);

  &:last-child {
    border-right: none;
  }

  &.is-today {
    background: color-mix(in srgb, var(--color-primary) 5%, transparent);
  }

  &.is-weekend:not(.is-today) {
    background: color-mix(in srgb, var(--bg-soft) 50%, transparent);
  }
}

.cotask-gantt__today {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 0;
  margin-left: 0;
  border-left: 1px dashed color-mix(in srgb, var(--color-danger) 70%, transparent);
  z-index: 0;
  pointer-events: none;
}

.cotask-gantt__bar-anchor {
  position: absolute;
  z-index: 2;
  box-sizing: border-box;
  padding: 0 2px;
}

.cotask-gantt__bar-anchor :deep(.el-tooltip__trigger) {
  display: block;
  width: 100%;
  height: 100%;
}

/* ── Task blocks (aligned with TaskNodeCard) ── */
.cotask-gantt__bar {
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: 0;
  background: var(--bg-card);
  cursor: pointer;
  overflow: hidden;
  text-align: left;
  box-shadow: inset 0 0 0 1px var(--border-subtle);
  transition: box-shadow 0.15s ease, transform 0.12s ease;

  &:hover {
    z-index: 4;
    box-shadow:
      inset 0 0 0 1px color-mix(in srgb, var(--color-primary) 35%, var(--border-color)),
      var(--shadow-sm);
    transform: translateY(-1px);
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 1px;
  }

  &.is-done .cotask-gantt__bar-title {
    color: var(--text-secondary);
    text-decoration: line-through;
    text-decoration-color: var(--text-tertiary);
  }

  &.is-narrow .cotask-gantt__bar-body {
    padding-inline: 6px;
    gap: 4px;
  }
}

.cotask-gantt__bar-body {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 0 8px 3px;
  line-height: 1.2;
}

.cotask-gantt__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--text-tertiary);
}

.cotask-gantt__bar.status-in_progress .cotask-gantt__dot {
  background: var(--color-primary);
}

.cotask-gantt__bar.status-done .cotask-gantt__dot {
  background: var(--color-success);
}

.cotask-gantt__bar.status-blocked .cotask-gantt__dot {
  background: var(--color-danger);
}

.cotask-gantt__bar-title {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cotask-gantt__bar-dates {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
}

.cotask-gantt__chip {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.3;
  padding: 1px 6px;
  border-radius: 0;
  white-space: nowrap;
}

.cotask-gantt__chip--todo {
  background: var(--bg-soft);
  color: var(--text-secondary);
}

.cotask-gantt__chip--in_progress {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.cotask-gantt__chip--done {
  background: color-mix(in srgb, var(--color-success) 14%, transparent);
  color: #15803d;
}

.cotask-gantt__chip--blocked {
  background: color-mix(in srgb, var(--color-danger) 12%, transparent);
  color: var(--color-danger);
}

.cotask-gantt__prog {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 4px;
  height: 3px;
  border-radius: 0;
  background: var(--bg-soft);
  overflow: hidden;
  pointer-events: none;
}

.cotask-gantt__prog-fill {
  display: block;
  height: 100%;
  border-radius: 0;
  transition: width 0.2s ease;

  &--todo {
    background: var(--text-tertiary);
    opacity: 0.35;
  }

  &--in_progress {
    background: var(--color-primary);
  }

  &--done {
    background: var(--color-success);
  }

  &--blocked {
    background: var(--color-danger);
  }
}

.cotask-gantt__bar.is-narrow .cotask-gantt__prog {
  left: 6px;
  right: 6px;
}

</style>

<style lang="scss">
.cotask-gantt-popper.el-popper {
  padding: 0 !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-md) !important;
  background: var(--bg-card) !important;
  max-width: 360px;

  .el-popper__arrow {
    display: none !important;
  }
}

.gantt-tip {
  padding: var(--space-3) var(--space-4);
  color: var(--text-primary);
}

.gantt-tip__path {
  font-size: var(--fs-sm);
  line-height: 1.45;
  margin-bottom: var(--space-2);
  word-break: break-word;
  color: var(--text-secondary);
}

.gantt-tip__path-sep {
  margin: 0 3px;
  color: var(--text-tertiary);
  font-weight: 400;
}

.gantt-tip__path-seg {
  font-weight: 500;

  &.is-path-current {
    font-weight: 600;
    color: var(--text-primary);
  }
}

.gantt-tip__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-xs);
  line-height: 1.35;
  color: var(--text-secondary);

  li {
    display: flex;
    align-items: baseline;
    gap: var(--space-2);
  }
}

.gantt-tip__label {
  flex-shrink: 0;
  width: 2.5em;
  color: var(--text-tertiary);
}

.gantt-tip__status--in_progress {
  color: var(--color-primary);
  font-weight: 600;
}

.gantt-tip__status--done {
  color: var(--color-success);
  font-weight: 600;
}

.gantt-tip__status--blocked {
  color: var(--color-danger);
  font-weight: 600;
}

.gantt-tip__urgent {
  color: var(--color-warning);
  font-weight: 600;
}
</style>
