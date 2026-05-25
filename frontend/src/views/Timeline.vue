<template>
  <div class="timeline-page">
    <!-- Toolbar -->
    <div class="card toolbar">
      <div class="toolbar-row">
        <el-button-group class="view-switch">
          <el-button :icon="Files" @click="goTree">项目树</el-button>
          <el-button type="primary" :icon="Calendar">时间轴</el-button>
        </el-button-group>

        <div class="tb-section">
          <span class="tb-label">视图:</span>
          <el-radio-group v-model="view" size="default" @change="onViewChange">
            <el-radio-button label="week">周</el-radio-button>
            <el-radio-button label="month">月</el-radio-button>
          </el-radio-group>
        </div>

        <div class="tb-section">
          <span class="tb-label">日期:</span>
          <el-button-group>
            <el-button :icon="ArrowLeft" @click="shiftDate(-1)" />
            <el-button @click="goToday">今天</el-button>
            <el-button :icon="ArrowRight" @click="shiftDate(1)" />
          </el-button-group>
          <el-date-picker
            v-model="startDate"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            style="width: 160px"
            @change="loadTimeline"
          />
        </div>

        <div class="tb-section">
          <span class="tb-label">过滤:</span>
          <el-switch
            v-model="onlyMine"
            active-text="仅看与我相关"
            inline-prompt
          />
        </div>

        <div class="tb-spacer" />

        <div class="tb-section">
          <span class="muted tiny">{{ dateRangeLabel }}</span>
        </div>
      </div>
    </div>

    <!-- Body -->
    <div class="body-grid">
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
import GanttBoard from '@/components/timeline/GanttBoard.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const gid = computed(() => Number(route.params.gid))

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
.timeline-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.toolbar {
  padding: 12px 16px;
}
.toolbar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.tb-section {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tb-label {
  font-size: 13px;
  color: var(--text-secondary);
}
.tb-spacer { flex: 1; }

.body-grid {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 16px;
  align-items: start;
}

.board-col {
  padding: 12px;
  min-height: 500px;
  height: calc(100vh - 220px);
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
  gap: 12px;
  position: sticky;
  top: 0;
}

.side-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.legend {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
  }
  .dot {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    flex-shrink: 0;
  }
  .dot-todo        { background: #9CA3AF; }
  .dot-in_progress { background: var(--color-primary); }
  .dot-done        { background: var(--color-success); }
  .dot-blocked     { background: var(--color-danger); }
  .dot-urgent      {
    background: transparent;
    border: 2px dashed var(--color-warning);
  }
}

.stats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    padding: 6px 0;
    border-bottom: 1px dashed var(--border-color);
    &:last-child { border-bottom: none; }
    b {
      font-size: 18px;
      font-weight: 700;
      color: var(--text-primary);
      &.is-urgent { color: var(--color-warning); }
    }
  }
}

.loading-wrap { padding: 16px; }

@media (max-width: 992px) {
  .body-grid { grid-template-columns: 1fr; }
  .side-col {
    position: static;
    flex-direction: row;
    overflow-x: auto;
    & > .card { min-width: 240px; }
  }
}

@media (max-width: 768px) {
  .toolbar-row > * {
    width: 100%;
  }
  .toolbar-row .tb-section { flex-wrap: wrap; }
  .board-col { height: auto; min-height: 420px; }
}
</style>
