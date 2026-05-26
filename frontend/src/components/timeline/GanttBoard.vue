<template>
  <div ref="containerRef" class="gantt-board"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Timeline } from 'vis-timeline/standalone'
import { DataSet } from 'vis-data'
import 'vis-timeline/styles/vis-timeline-graph2d.min.css'
import type { GroupRow } from '@/api'

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

const containerRef = ref<HTMLElement | null>(null)
let timeline: Timeline | null = null
let itemsDS: DataSet<any> | null = null
let groupsDS: DataSet<any> | null = null

// NOTE: Dependency arrows between blocks are intentionally skipped in v1.0.
// vis-timeline does not support arrows natively; would require a custom overlay.

function buildGroups(rows: GroupRow[]) {
  return rows.map((r) => ({
    id: r.user_id,
    content: `
      <div class="g-row">
        ${
          r.avatar_url
            ? `<img class="g-avatar" src="${escapeAttr(r.avatar_url)}" alt="" />`
            : `<span class="g-avatar g-avatar-fallback">${escapeHtml((r.name || '?').slice(0, 1))}</span>`
        }
        <span class="g-name">${escapeHtml(r.name || '未命名')}</span>
        ${r.role === 'leader' ? '<span class="g-role">组长</span>' : ''}
      </div>
    `,
  }))
}

function buildItems(rows: GroupRow[]) {
  const items: any[] = []
  for (const r of rows) {
    for (const b of r.blocks) {
      if (!b.start_date || !b.end_date) continue
      items.push({
        id: `${r.user_id}-${b.task_id}`,
        taskId: b.task_id,
        group: r.user_id,
        content: `<span class="b-title">${escapeHtml(b.title || '未命名任务')}</span>`,
        start: b.start_date,
        end: b.end_date,
        title: `${b.title} · ${b.progress}%`,
        className: `b-block status-${b.status}${b.urgent ? ' urgent' : ''}`,
      })
    }
  }
  return items
}

function escapeHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
function escapeAttr(s: string): string {
  return String(s).replace(/"/g, '&quot;')
}

function getTimeAxis(view: 'week' | 'month') {
  return view === 'week'
    ? { scale: 'day', step: 1 }
    : { scale: 'week', step: 1 }
}

function mount() {
  if (!containerRef.value) return
  groupsDS = new DataSet(buildGroups(props.rows))
  itemsDS = new DataSet(buildItems(props.rows))
  timeline = new Timeline(containerRef.value, itemsDS, groupsDS, {
    orientation: 'top',
    stack: false,
    zoomable: true,
    moveable: false,
    selectable: true,
    showCurrentTime: true,
    locale: 'zh-cn',
    timeAxis: getTimeAxis(props.view),
    margin: { item: 6, axis: 8 },
    min: props.start,
    max: props.end,
    start: props.start,
    end: props.end,
  } as any)
  timeline.on('click', (p: any) => {
    if (p?.item == null || !itemsDS) return
    const it = itemsDS.get(p.item) as any
    if (it?.taskId != null) emit('blockClick', it.taskId)
  })
}

function refreshData() {
  if (!groupsDS || !itemsDS) return
  groupsDS.clear()
  groupsDS.add(buildGroups(props.rows))
  itemsDS.clear()
  itemsDS.add(buildItems(props.rows))
}

function refreshWindow() {
  if (!timeline) return
  timeline.setOptions({ timeAxis: getTimeAxis(props.view) } as any)
  timeline.setWindow(props.start, props.end, { animation: true })
}

onMounted(() => {
  mount()
})

watch(() => props.rows, () => refreshData(), { deep: true })
watch(() => [props.start, props.end, props.view], () => refreshWindow())

onBeforeUnmount(() => {
  if (timeline) {
    timeline.destroy()
    timeline = null
  }
  itemsDS = null
  groupsDS = null
})
</script>

<style lang="scss" scoped>
.gantt-board {
  width: 100%;
  height: 100%;
  min-height: 380px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  overflow: hidden;
}
</style>

<style lang="scss">
/* unscoped overrides for vis-timeline internals */
.gantt-board {
  /* row label cell */
  .g-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 6px;
  }
  .g-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    object-fit: cover;
    background: var(--bg-soft);
  }
  .g-avatar-fallback {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }
  .g-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .g-role {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: var(--radius-full);
    background: rgba(230, 162, 60, 0.16);
    color: var(--color-warning);
    font-weight: 600;
  }

  /* vis structural */
  .vis-timeline {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-family: inherit;
    color: var(--text-primary);
    background: var(--bg-card);
  }
  .vis-panel.vis-left,
  .vis-panel.vis-top,
  .vis-panel.vis-bottom {
    border-color: var(--border-color);
    background: var(--bg-soft);
  }
  .vis-labelset .vis-label,
  .vis-foreground .vis-group {
    border-color: var(--border-color);
  }
  .vis-time-axis .vis-text {
    color: var(--text-secondary);
    font-size: 11px;
  }
  .vis-time-axis .vis-grid.vis-minor {
    border-color: var(--border-color);
  }
  .vis-time-axis .vis-grid.vis-major {
    border-color: var(--border-color);
  }
  .vis-current-time {
    background: var(--color-danger);
    width: 2px;
  }

  /* item blocks: solid color by status */
  .vis-item.b-block {
    border-radius: 6px;
    border: none;
    color: #fff;
    font-size: 12px;
    padding: 2px 6px;
    cursor: pointer;
    transition: filter .15s ease, transform .15s ease;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    .b-title {
      display: inline-block;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    &:hover {
      filter: brightness(1.05);
      transform: translateY(-1px);
    }
  }
  .vis-item.b-block .vis-item-content { padding: 0; }

  .vis-item.status-todo {
    background: #9CA3AF;
    color: #fff;
  }
  .vis-item.status-in_progress {
    background: var(--color-primary);
  }
  .vis-item.status-done {
    background: var(--color-success);
  }
  .vis-item.status-blocked {
    background: var(--color-danger);
  }

  /* urgent dashed warning border */
  .vis-item.b-block.urgent {
    box-shadow: 0 0 0 2px var(--color-warning);
    border: 2px dashed var(--color-warning) !important;
    padding: 0 4px;
  }

  .vis-item.vis-selected {
    box-shadow: 0 0 0 2px var(--color-primary);
  }
}

html.dark .gantt-board {
  .vis-item.status-todo { background: #4B5563; }
  .vis-time-axis .vis-text { color: var(--text-tertiary); }
}
</style>
