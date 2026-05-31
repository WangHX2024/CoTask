<template>
  <div class="timeline-page">
    <!-- Sticky toolbar — same pattern as ProjectTree -->
    <header class="ws-toolbar tl-toolbar">
      <div class="ws-toolbar__left">
        <h1 class="ws-toolbar__title">
          <span class="t-main">时间轴</span>
          <template v-if="group">
            <span class="t-sep">/</span>
            <span class="t-course">{{ group.course_name }}</span>
            <span class="t-sep">/</span>
            <span class="t-name">{{ group.name }}</span>
          </template>
        </h1>
        <span class="ws-toolbar__sep" aria-hidden="true" />
        <TreeTimelineSwitcher mode="timeline" :group-id="gid" />
      </div>

      <div class="ws-toolbar__right">
        <div class="tl-date-controls">
          <div class="tl-date-nav" role="group" aria-label="日期导航">
            <button
              type="button"
              class="ws-chip ws-chip--icon"
              aria-label="上一段"
              @click="shiftDate(-1)"
            >
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <button type="button" class="ws-chip" @click="goToday">今天</button>
            <button
              type="button"
              class="ws-chip ws-chip--icon"
              aria-label="下一段"
              @click="shiftDate(1)"
            >
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
          <span class="ws-toolbar__sep ws-toolbar__sep--compact" aria-hidden="true" />
          <el-date-picker
            v-model="startDate"
            class="tl-date-picker"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="loadTimeline"
          />
        </div>

        <span class="ws-toolbar__sep" aria-hidden="true" />

        <SegmentedControl
          v-model="view"
          size="sm"
          :options="viewOptions"
          @change="onViewChange"
        />

        <span class="ws-toolbar__sep" aria-hidden="true" />

        <button
          type="button"
          class="ws-chip"
          :class="{ 'is-active': onlyMine }"
          :aria-pressed="onlyMine"
          @click="onlyMine = !onlyMine"
        >
          <el-icon><Filter /></el-icon>
          仅我的
        </button>

        <span class="ws-toolbar__sep" aria-hidden="true" />

        <span
          class="ws-meta-label tl-range-label"
          :title="dateRangeLabel"
        >{{ dateRangeLabel }}</span>
      </div>
    </header>

    <!-- Body -->
    <div class="tl-body">
      <!-- Gantt board -->
      <section class="tl-board">
        <div v-if="loading" class="tl-board__state">
          <el-skeleton :rows="8" animated />
        </div>
        <template v-else-if="!filteredRows.length">
          <div class="tl-board__state">
            <el-empty description="此区间内没有任务" :image-size="120" />
          </div>
        </template>
        <GanttBoard
          v-else
          :rows="filteredRows"
          :start="rangeStart"
          :end="rangeEnd"
          :view="view"
          @blockClick="onBlockClick"
        />
      </section>

      <!-- Side panel -->
      <aside class="side-col">
        <div class="card legend-card">
          <div class="side-title">图例</div>
          <ul class="legend">
            <li>
              <span class="dot dot-todo"></span>
              <span>待办</span>
            </li>
            <li>
              <span class="dot dot-in_progress"></span>
              <span>进行中</span>
            </li>
            <li>
              <span class="dot dot-done"></span>
              <span>已完成</span>
            </li>
            <li>
              <span class="dot dot-blocked"></span>
              <span>已阻塞</span>
            </li>
            <li>
              <span class="dot dot-urgent"></span>
              <span>紧急任务</span>
            </li>
          </ul>
        </div>

        <div class="card summary-card">
          <div class="side-title">本区间统计</div>
          <ul class="stats">
            <li>
              <span class="muted">总任务数</span>
              <b>{{ totalCount }}</b>
            </li>
            <li>
              <span class="muted">紧急任务</span>
              <b :class="{ 'is-urgent': urgentCount > 0 }">{{ urgentCount }}</b>
            </li>
            <li>
              <span class="muted">进行中</span>
              <b>{{ inProgressCount }}</b>
            </li>
            <li>
              <span class="muted">已完成</span>
              <b>{{ doneCount }}</b>
            </li>
            <li>
              <span class="muted">已阻塞</span>
              <b>{{ blockedCount }}</b>
            </li>
          </ul>
        </div>
      </aside>
    </div>

    <TaskDrawer
      v-model:visible="drawerOpen"
      :node="treeStore.selected"
      :members="members"
      :group="group"
      @select="onSelectNode"
      @add-child="onAddChild"
    />
  </div>
</template>


<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Filter } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type GroupRow, type MemberInfo, type TimelineResponse } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import { useTreeStore } from '@/stores/tree'
import { useWS } from '@/composables/useWS'
import GanttBoard from '@/components/timeline/GanttBoard.vue'
import TaskDrawer from '@/components/tree/TaskDrawer.vue'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import TreeTimelineSwitcher from '@/components/common/TreeTimelineSwitcher.vue'

const viewOptions = [
  { label: '周视图', value: 'week' as const },
  { label: '月视图', value: 'month' as const },
]

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()
const treeStore = useTreeStore()
const ws = useWS()

const gid = computed(() => Number(route.params.gid))
const group = computed(() => groupsStore.list.find((g) => g.id === gid.value) || null)

const members = ref<MemberInfo[]>([])
const drawerOpen = ref(false)

const loading = ref(true)
const view = ref<'week' | 'month'>('week')
const startDate = ref<string>(dayjs().format('YYYY-MM-DD'))
const onlyMine = ref(false)
const rows = ref<GroupRow[]>([])
const rangeStart = ref<string>('')
const rangeEnd = ref<string>('')

const dateRangeLabel = computed(() => {
  if (!rangeStart.value || !rangeEnd.value) return ''
  const s = dayjs(rangeStart.value)
  const e = dayjs(rangeEnd.value)
  const endFmt = s.year() === e.year() ? 'M月D日' : 'YYYY年M月D日'
  return `${s.format('YYYY年M月D日')} — ${e.format(endFmt)}`
})

const filteredRows = computed<GroupRow[]>(() => {
  if (!onlyMine.value || !auth.user) return rows.value
  return rows.value.filter((r) => r.user_id === auth.user!.id)
})

// summary numbers, computed against filtered rows
const totalCount = computed(() =>
  filteredRows.value.reduce((acc, r) => acc + r.blocks.length, 0),
)
const urgentCount = computed(() =>
  filteredRows.value.reduce(
    (acc, r) => acc + r.blocks.filter((b) => b.urgent).length,
    0,
  ),
)
const inProgressCount = computed(() =>
  filteredRows.value.reduce(
    (acc, r) => acc + r.blocks.filter((b) => b.status === 'in_progress').length,
    0,
  ),
)
const doneCount = computed(() =>
  filteredRows.value.reduce(
    (acc, r) => acc + r.blocks.filter((b) => b.status === 'done').length,
    0,
  ),
)
const blockedCount = computed(() =>
  filteredRows.value.reduce(
    (acc, r) => acc + r.blocks.filter((b) => b.status === 'blocked').length,
    0,
  ),
)

async function loadTimeline() {
  if (!gid.value) return
  loading.value = true
  try {
    const data: TimelineResponse = await Api.timeline(gid.value, view.value, startDate.value)
    rows.value = data.rows || []
    rangeStart.value = data.start || startDate.value
    rangeEnd.value =
      data.end ||
      dayjs(startDate.value)
        .add(view.value === 'week' ? 6 : 30, 'day')
        .format('YYYY-MM-DD')
    if (data.start) startDate.value = data.start
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载时间轴失败')
  } finally {
    loading.value = false
  }
}

function onViewChange() {
  void loadTimeline()
}

function shiftDate(direction: number) {
  const unit = view.value === 'week' ? 'week' : 'month'
  startDate.value = dayjs(startDate.value).add(direction, unit).format('YYYY-MM-DD')
  void loadTimeline()
}

function goToday() {
  startDate.value = dayjs().format('YYYY-MM-DD')
  void loadTimeline()
}

async function ensureTreeLoaded(): Promise<boolean> {
  if (!gid.value) return false
  if (treeStore.groupId === gid.value && treeStore.nodes.length > 0) return true
  try {
    await treeStore.load(gid.value)
    return true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载任务数据失败')
    return false
  }
}

async function onBlockClick(taskId: number) {
  if (!(await ensureTreeLoaded())) return
  if (!treeStore.byId.get(taskId)) {
    ElMessage.warning('任务不存在或已删除')
    return
  }
  treeStore.setSelected(taskId)
  drawerOpen.value = true
}

function onSelectNode(id: number) {
  treeStore.setSelected(id)
  drawerOpen.value = true
}

function onAddChild(parentId: number) {
  drawerOpen.value = false
  router.push({
    path: `/groups/${gid.value}/tree`,
    query: { select: String(parentId) },
  })
}

async function refreshMembers() {
  if (!gid.value) return
  try {
    members.value = await Api.members(gid.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载成员失败')
  }
}

const unsubs: Array<() => void> = []

onMounted(async () => {
  if (!gid.value) return
  groupsStore.setCurrent(gid.value)
  if (!groupsStore.loaded) {
    try { await groupsStore.refresh() } catch {}
  }
  await Promise.all([loadTimeline(), ensureTreeLoaded(), refreshMembers()])

  const sel = Number(route.query.select)
  if (sel && treeStore.byId.get(sel)) {
    treeStore.setSelected(sel)
    drawerOpen.value = true
  }

  unsubs.push(
    ws.on('tree.updated', (data: unknown) => {
      const d = data as { group_id?: number }
      if (d?.group_id && Number(d.group_id) === gid.value) {
        treeStore.applyWSPatch(data)
        void loadTimeline()
      }
    }),
  )
  unsubs.push(
    ws.on('task.status_changed', (data: unknown) => {
      const d = data as { group_id?: number }
      if (d?.group_id && Number(d.group_id) === gid.value) {
        void treeStore.load(gid.value)
        void loadTimeline()
      }
    }),
  )
})

onUnmounted(() => {
  for (const u of unsubs) {
    try { u() } catch {}
  }
})

watch(gid, async (val, old) => {
  if (!val || val === old) return
  groupsStore.setCurrent(val)
  drawerOpen.value = false
  treeStore.setSelected(0)
  await Promise.all([loadTimeline(), ensureTreeLoaded(), refreshMembers()])
})
</script>

<style lang="scss" scoped>
/* ========================================================
   Timeline — workspace layout matching ProjectTree
   ======================================================== */
.timeline-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Fixed width so toolbar chips (e.g. 仅我的) do not shift when the range text changes */
.tl-range-label {
  flex: 0 0 12rem;
  width: 12rem;
  text-align: center;
  font-variant-numeric: tabular-nums;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---------- Body (gantt + side panel) ---------- */
.tl-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-6);
  padding: var(--space-6);
  overflow: auto;
  align-items: start;
}

.tl-board {
  min-height: 480px;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.tl-board__state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  min-height: 360px;
}

.side-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  position: sticky;
  top: 0;
}

.side-title {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-3);
}

/* ---------- Legend ---------- */
.legend {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);

  li {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--fs-sm);
    color: var(--text-secondary);
  }

  .dot {
    width: 13px;
    height: 13px;
    border-radius: var(--radius-xs);
    flex-shrink: 0;
  }

  .dot-todo        { background: var(--text-tertiary); }
  .dot-in_progress { background: var(--color-primary); }
  .dot-done        { background: var(--color-success); }
  .dot-blocked     { background: var(--color-danger); }
  .dot-urgent      { background: var(--color-warning); }
}

/* ---------- Stats ---------- */
.stats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: var(--fs-sm);
    color: var(--text-secondary);
    padding: 6px 0;
    border-bottom: 1px solid var(--border-subtle);

    &:last-child { border-bottom: none; }

    b {
      font-size: var(--fs-lg);
      font-weight: 700;
      color: var(--text-primary);
      &.is-urgent { color: var(--color-warning); }
    }
  }
}

/* ---------- Responsive ---------- */
@media (max-width: 1100px) {
  .tl-body { grid-template-columns: 1fr; }
  .side-col {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-3);
  }
}

@media (max-width: 768px) {
  .ws-toolbar { padding: var(--space-3) var(--space-4); }
  .side-col { grid-template-columns: 1fr; }
}
</style>
