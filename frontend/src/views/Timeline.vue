<template>
  <div class="timeline-page">
    <!-- Sticky toolbar — same pattern as ProjectTree -->
    <header class="tl-toolbar">
      <div class="tb-left">
        <h1 class="tl-title">
          <span class="t-main">时间轴</span>
          <template v-if="group">
            <span class="t-sep">/</span>
            <span class="t-course">{{ group.course_name }}</span>
            <span class="t-sep">/</span>
            <span class="t-name">{{ group.name }}</span>
          </template>
        </h1>

        <div class="view-switcher">
          <el-button-group>
            <el-button size="small" @click="goTree">
              <el-icon><Files /></el-icon>&nbsp;项目树
            </el-button>
            <el-button size="small" type="primary">
              <el-icon><Calendar /></el-icon>&nbsp;时间轴
            </el-button>
          </el-button-group>
        </div>
      </div>

      <div class="tb-right">
        <!-- Date navigation -->
        <el-button-group size="small">
          <el-button :icon="ArrowLeft" @click="shiftDate(-1)" />
          <el-button @click="goToday">今天</el-button>
          <el-button :icon="ArrowRight" @click="shiftDate(1)" />
        </el-button-group>
        <el-date-picker
          v-model="startDate"
          type="date"
          value-format="YYYY-MM-DD"
          :clearable="false"
          style="width: 148px"
          @change="loadTimeline"
        />

        <div class="tb-divider" />

        <!-- View -->
        <SegmentedControl
          v-model="view"
          size="sm"
          :options="viewOptions"
          @change="onViewChange"
        />

        <div class="tb-divider" />

        <!-- Filter -->
        <el-switch
          v-model="onlyMine"
          active-text="仅我的"
          inline-prompt
          style="--el-switch-on-color: var(--color-primary);"
        />

        <!-- Date range label -->
        <span class="date-range-label">{{ dateRangeLabel }}</span>
      </div>
    </header>

    <!-- Body -->
    <div class="tl-body">
      <!-- Gantt board -->
      <section class="board-col card">
        <div v-if="loading" class="loading-wrap">
          <el-skeleton :rows="8" animated />
        </div>
        <template v-else-if="!filteredRows.length">
          <el-empty description="此区间内没有任务" :image-size="120" />
        </template>
        <template v-else>
          <GanttBoard
            :rows="filteredRows"
            :start="rangeStart"
            :end="rangeEnd"
            :view="view"
            @blockClick="onBlockClick"
          />
        </template>
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
              <span>紧急 (虚线)</span>
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
              <span class="muted">阻塞</span>
              <b>{{ blockedCount }}</b>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>


<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Calendar, Files } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type GroupRow, type TimelineResponse } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import GanttBoard from '@/components/timeline/GanttBoard.vue'
import SegmentedControl from '@/components/common/SegmentedControl.vue'

const viewOptions = [
  { label: '周视图', value: 'week' as const },
  { label: '月视图', value: 'month' as const },
]

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()

const gid = computed(() => Number(route.params.gid))
const group = computed(() => groupsStore.list.find((g) => g.id === gid.value) || null)

const loading = ref(true)
const view = ref<'week' | 'month'>('week')
const startDate = ref<string>(dayjs().format('YYYY-MM-DD'))
const onlyMine = ref(false)
const rows = ref<GroupRow[]>([])
const rangeStart = ref<string>('')
const rangeEnd = ref<string>('')

const dateRangeLabel = computed(() => {
  if (!rangeStart.value || !rangeEnd.value) return ''
  return `${dayjs(rangeStart.value).format('YYYY-MM-DD')} ~ ${dayjs(rangeEnd.value).format('YYYY-MM-DD')}`
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
        .add(view.value === 'week' ? 7 : 30, 'day')
        .format('YYYY-MM-DD')
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

function goTree() {
  router.push(`/groups/${gid.value}/tree`)
}

function onBlockClick(taskId: number) {
  router.push({
    path: `/groups/${gid.value}/tree`,
    query: { select: String(taskId) },
  })
}

onMounted(() => {
  void loadTimeline()
})

// reload if gid changes (group switch)
watch(gid, (val, old) => {
  if (val && val !== old) void loadTimeline()
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

/* ---------- Sticky toolbar (identical pattern to ProjectTree) ---------- */
.tl-toolbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  height: 56px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.tb-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.tb-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.tb-divider {
  width: 1px;
  height: 18px;
  background: var(--border-subtle);
  flex-shrink: 0;
  margin: 0 var(--space-1);
}

/* Breadcrumb title */
.tl-title {
  margin: 0;
  font-size: var(--fs-base);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  overflow: hidden;

  .t-main   { color: var(--text-primary); }
  .t-sep    { color: var(--text-tertiary); font-weight: 400; font-size: var(--fs-sm); }
  .t-course { color: var(--color-primary); overflow: hidden; text-overflow: ellipsis; max-width: 120px; }
  .t-name   { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
}

.view-switcher { flex-shrink: 0; }

.date-range-label {
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  white-space: nowrap;
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

.board-col {
  padding: var(--space-3);
  min-height: 480px;
  display: flex;
  flex-direction: column;

  & > * {
    flex: 1;
    min-height: 0;
  }
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
  .dot-urgent      { background: transparent; border: 2px dashed var(--color-warning); }
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

.loading-wrap { padding: var(--space-4); }

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
  .tl-toolbar { height: auto; padding: var(--space-3) var(--space-4); }
  .tb-left, .tb-right { flex-wrap: wrap; }
  .tl-title .t-course, .tl-title .t-name { display: none; }
  .side-col { grid-template-columns: 1fr; }
}
</style>
