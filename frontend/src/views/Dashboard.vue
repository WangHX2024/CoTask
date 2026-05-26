<template>
  <div class="dashboard page">
    <!-- Urgent banner -->
    <div v-if="!loading && urgent.length" class="urgent-banner urgent-bg">
      <el-icon class="ub-icon"><Warning /></el-icon>
      <div class="ub-text">
        <strong>{{ urgent.length }} 个任务临近 DDL</strong>
        <span class="ub-list">
          {{ urgent.slice(0, 3).map((t) => t.title).join('、') }}
          <span v-if="urgent.length > 3"> 等</span>
        </span>
      </div>
      <el-button
        size="small"
        type="danger"
        plain
        @click="scrollToTodos"
      >立即处理</el-button>
    </div>

    <!-- AI Daily Advice -->
    <section class="advice-card" :class="{ 'advice-loading': adviceLoading }">
      <div class="advice-bg" aria-hidden="true"></div>
      <div class="advice-inner">
        <div class="advice-head">
          <div class="advice-title">
            <el-icon class="sparkle"><MagicStick /></el-icon>
            <span>AI 今日建议</span>
            <el-tag
              v-if="advice?.cached"
              size="small"
              type="info"
              effect="plain"
              class="cached-tag"
            >缓存</el-tag>
          </div>
          <el-button
            size="small"
            text
            class="refresh-btn"
            :loading="adviceLoading"
            @click="loadAdvice(true)"
          >
            <el-icon><Refresh /></el-icon>&nbsp;刷新建议
          </el-button>
        </div>

        <template v-if="adviceLoading && !advice">
          <el-skeleton :rows="3" animated />
        </template>
        <template v-else-if="advice">
          <p class="advice-text">{{ advice.advice }}</p>
          <ul v-if="advice.suggestions?.length" class="advice-list">
            <li v-for="(s, i) in advice.suggestions" :key="i">
              <el-icon class="bullet"><Check /></el-icon>
              <span>{{ s }}</span>
            </li>
          </ul>
          <div v-if="advice.generated_at" class="advice-foot">
            生成于 {{ relativeTime(advice.generated_at) }}
          </div>
        </template>
      </div>
    </section>

    <!-- Two column: calendar + todos -->
    <div class="main-grid">
      <!-- LEFT: mini calendar -->
      <aside class="calendar-col">
        <div class="card calendar-card">
          <div class="card-head">
            <div class="card-title">
              <el-icon><Calendar /></el-icon> 本周日历
            </div>
            <div class="muted tiny">{{ weekRangeLabel }}</div>
          </div>
          <div class="cal-grid">
            <div
              v-for="d in weekDays"
              :key="d.iso"
              class="cal-day"
              :class="{ today: d.isToday, has: d.count > 0 }"
              @click="onPickDay(d.iso)"
            >
              <div class="cal-wd">{{ d.wd }}</div>
              <div class="cal-num">{{ d.dom }}</div>
              <div v-if="d.count > 0" class="cal-badge">{{ d.count }}</div>
            </div>
          </div>
          <div class="cal-legend tiny muted">
            <span><i class="dot dot-today"></i> 今天</span>
            <span><i class="dot dot-has"></i> 有 DDL</span>
          </div>
        </div>
      </aside>

      <!-- RIGHT: todo list -->
      <section class="todos-col" ref="todosColRef">
        <div class="card todos-card">
          <div class="card-head">
            <div class="card-title">
              <el-icon><List /></el-icon> 我的待办
              <el-tag
                v-if="!loading"
                size="small"
                type="info"
                effect="plain"
                class="count-tag"
              >{{ openTasks.length }} 项</el-tag>
            </div>
            <SegmentedControl
              v-model="todoFilter"
              size="sm"
              :options="todoFilterOptions"
            />
          </div>

          <template v-if="loading">
            <el-skeleton :rows="5" animated />
          </template>
          <template v-else-if="filteredTasks.length === 0">
            <el-empty description="暂无待办，去看看时间轴吧" :image-size="100" />
          </template>
          <template v-else>
            <ul class="todo-list">
              <li
                v-for="t in filteredTasks"
                :key="`${t.group_id}-${t.task_id}`"
                class="todo-row"
                :class="{ done: t.status === 'done', urgent: t.urgent }"
              >
                <div class="todo-main">
                  <div class="todo-meta">
                    <span class="course-chip" :style="courseChipStyle(t.course_name)">
                      {{ t.course_name }}
                    </span>
                    <span class="group-name muted">{{ t.group_name }}</span>
                  </div>
                  <div class="todo-title">{{ t.title }}</div>
                  <div class="todo-sub">
                    <span class="ddl" :class="{ 'is-urgent': t.urgent, 'is-overdue': t.days_left < 0 }">
                      <el-icon><Clock /></el-icon> {{ ddlLabel(t) }}
                    </span>
                    <span class="status-pill" :class="`status-${t.status}`">
                      {{ statusLabel(t.status) }}
                    </span>
                  </div>
                </div>

                <div class="todo-actions">
                  <el-button
                    v-if="t.status !== 'done'"
                    size="small"
                    type="success"
                    plain
                    :loading="doneBusy[`${t.group_id}-${t.task_id}`]"
                    @click="onMarkDone(t)"
                  >
                    <el-icon><Check /></el-icon>&nbsp;完成
                  </el-button>
                  <el-button
                    size="small"
                    @click="onEnter(t)"
                  >
                    进入
                    <el-icon><Right /></el-icon>
                  </el-button>
                </div>
              </li>
            </ul>
          </template>
        </div>
      </section>
    </div>

    <!-- Leader groups row -->
    <section v-if="!loading && leaderGroups.length" class="leader-row">
      <div class="section-head">
        <div class="card-title">
          <el-icon><Trophy /></el-icon> 我管理的小组
        </div>
        <div class="muted tiny">作为组长，请关注下面小组的进度</div>
      </div>
      <div class="leader-grid">
        <div
          v-for="g in leaderGroups"
          :key="g.group_id"
          class="card leader-card"
          @click="onEnterGroup(g.group_id)"
        >
          <div class="leader-head">
            <div class="leader-titles">
              <div class="course-chip" :style="courseChipStyle(g.course_name)">
                {{ g.course_name }}
              </div>
              <div class="leader-name">{{ g.name }}</div>
            </div>
            <div
              v-if="g.urgent_count > 0"
              class="badge badge--danger badge--pill"
              :title="`${g.urgent_count} 个紧急任务`"
            >
              <el-icon><Warning /></el-icon> {{ g.urgent_count }}
            </div>
          </div>

          <div class="leader-body">
            <div class="ring-wrap">
              <svg viewBox="0 0 64 64" class="ring">
                <circle cx="32" cy="32" r="28" class="ring-track" />
                <circle
                  cx="32"
                  cy="32"
                  r="28"
                  class="ring-fill"
                  :stroke-dasharray="`${ringLen(g.progress)} ${ringCirc - ringLen(g.progress)}`"
                />
                <text x="32" y="36" text-anchor="middle" class="ring-text">
                  {{ Math.round(g.progress) }}%
                </text>
              </svg>
            </div>
            <ul class="counts">
              <li><span class="status-pill status-todo">待办</span><b>{{ g.todo }}</b></li>
              <li><span class="status-pill status-in_progress">进行</span><b>{{ g.in_progress }}</b></li>
              <li><span class="status-pill status-done">完成</span><b>{{ g.done }}</b></li>
              <li><span class="status-pill status-blocked">阻塞</span><b>{{ g.blocked }}</b></li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Warning, MagicStick, Refresh, Check, Calendar, List, Clock,
  Right, Trophy,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type DashTask, type LeaderGroup, type AdviceResponse } from '@/api'
import SegmentedControl from '@/components/common/SegmentedControl.vue'

const router = useRouter()

const todoFilterOptions = [
  { label: '未完成', value: 'open' as const },
  { label: '全部', value: 'all' as const },
]

// ---------- state ----------
const loading = ref(true)
const tasks = ref<DashTask[]>([])
const urgent = ref<DashTask[]>([])
const leaderGroups = ref<LeaderGroup[]>([])
const todoFilter = ref<'open' | 'all'>('open')
const doneBusy = reactive<Record<string, boolean>>({})

const advice = ref<AdviceResponse | null>(null)
const adviceLoading = ref(false)

const todosColRef = ref<HTMLElement | null>(null)

// ---------- load ----------
async function loadDashboard() {
  loading.value = true
  try {
    const data = await Api.dashboard()
    tasks.value = (data.tasks || []).slice().sort((a, b) => a.days_left - b.days_left)
    urgent.value = data.urgent || []
    leaderGroups.value = data.leader_groups || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载首页数据失败')
  } finally {
    loading.value = false
  }
}

async function loadAdvice(forceMsg = false) {
  adviceLoading.value = true
  try {
    advice.value = await Api.advice()
    if (forceMsg) ElMessage.success('建议已刷新')
  } catch (e: any) {
    if (forceMsg) ElMessage.error(e?.response?.data?.message || '获取建议失败')
  } finally {
    adviceLoading.value = false
  }
}

onMounted(() => {
  void loadDashboard()
  void loadAdvice()
})

// ---------- derived: tasks ----------
const openTasks = computed(() => tasks.value.filter((t) => t.status !== 'done'))
const filteredTasks = computed(() =>
  todoFilter.value === 'open' ? openTasks.value : tasks.value,
)

// ---------- helpers ----------
function statusLabel(s: string) {
  return ({ todo: '待办', in_progress: '进行中', done: '已完成', blocked: '已阻塞' } as Record<string, string>)[s] || s
}

function ddlLabel(t: DashTask): string {
  const d = t.days_left
  if (!t.end_date) return '无截止日期'
  if (d < 0) return `已逾期 ${Math.abs(d)} 天`
  if (d === 0) return '今天截止'
  if (d === 1) return '明天'
  if (d === 2) return '后天'
  if (d <= 7) return `${d} 天后`
  return dayjs(t.end_date).format('MM-DD')
}

function relativeTime(iso: string): string {
  const t = dayjs(iso)
  const now = dayjs()
  const diffMin = now.diff(t, 'minute')
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = now.diff(t, 'hour')
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffD = now.diff(t, 'day')
  if (diffD < 7) return `${diffD} 天前`
  return t.format('YYYY-MM-DD HH:mm')
}

// course hash chip color
const palette = [
  { bg: 'rgba(61,126,255,0.12)',  fg: '#1D4ED8' },
  { bg: 'rgba(245,108,108,0.12)', fg: '#B91C1C' },
  { bg: 'rgba(103,194,58,0.14)',  fg: '#15803D' },
  { bg: 'rgba(230,162,60,0.14)',  fg: '#B45309' },
  { bg: 'rgba(159,122,234,0.14)', fg: '#6D28D9' },
  { bg: 'rgba(20,184,166,0.14)',  fg: '#0F766E' },
  { bg: 'rgba(236,72,153,0.14)',  fg: '#BE185D' },
  { bg: 'rgba(99,102,241,0.14)',  fg: '#4338CA' },
]
function hashStr(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0
  return Math.abs(h)
}
function courseChipStyle(name: string) {
  const p = palette[hashStr(name || '?') % palette.length]
  return { background: p.bg, color: p.fg }
}

// ---------- mini calendar ----------
interface WeekDay { iso: string; wd: string; dom: number; isToday: boolean; count: number }
const WEEK_LABELS = ['一', '二', '三', '四', '五', '六', '日']
const weekStart = computed(() => dayjs().startOf('day').day(1)) // Monday
const weekDays = computed<WeekDay[]>(() => {
  const today = dayjs().startOf('day')
  const counts: Record<string, number> = {}
  for (const t of tasks.value) {
    if (!t.end_date) continue
    const key = dayjs(t.end_date).format('YYYY-MM-DD')
    counts[key] = (counts[key] || 0) + 1
  }
  return Array.from({ length: 7 }, (_, i) => {
    const d = weekStart.value.add(i, 'day')
    const iso = d.format('YYYY-MM-DD')
    return {
      iso,
      wd: WEEK_LABELS[i],
      dom: d.date(),
      isToday: d.isSame(today, 'day'),
      count: counts[iso] || 0,
    }
  })
})
const weekRangeLabel = computed(() => {
  const start = weekStart.value
  const end = start.add(6, 'day')
  return `${start.format('MM-DD')} ~ ${end.format('MM-DD')}`
})

function onPickDay(iso: string) {
  const match = tasks.value.find((t) => t.end_date && dayjs(t.end_date).format('YYYY-MM-DD') === iso)
  if (!match) return
  onEnter(match)
}

// ---------- actions ----------
async function onMarkDone(t: DashTask) {
  const key = `${t.group_id}-${t.task_id}`
  doneBusy[key] = true
  try {
    await Api.changeStatus(t.group_id, t.task_id, 'done')
    t.status = 'done'
    urgent.value = urgent.value.filter((u) => u.task_id !== t.task_id)
    ElMessage.success('任务已完成')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '更新失败')
  } finally {
    doneBusy[key] = false
  }
}

function onEnter(t: DashTask) {
  router.push({
    path: `/groups/${t.group_id}/tree`,
    query: { select: String(t.task_id) },
  })
}
function onEnterGroup(gid: number) {
  router.push(`/groups/${gid}/tree`)
}

function scrollToTodos() {
  todosColRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ---------- ring math ----------
const ringCirc = 2 * Math.PI * 28
function ringLen(progress: number) {
  return (Math.max(0, Math.min(100, progress)) / 100) * ringCirc
}
</script>

<style lang="scss" scoped>
/* Dashboard uses .page (global) for layout; only inner styles below */

/* ============================================================
   1. Urgent banner — flat alert strip
   ============================================================ */
.urgent-banner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-md);
  border: 1px solid rgba(239, 68, 68, 0.25);

  .ub-icon { font-size: 20px; flex-shrink: 0; }

  .ub-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);

    .ub-list { font-size: var(--fs-sm); opacity: 0.9; }
  }
}

/* ============================================================
   2. AI advice — gradient hero card
   ============================================================ */
.advice-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  color: var(--text-inverse);
  box-shadow: var(--shadow-md);

  .advice-bg {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #2563EB 0%, #4F46E5 55%, #7C3AED 100%);
    z-index: 0;
  }

  .advice-bg::after {
    content: '';
    position: absolute;
    width: 320px;
    height: 320px;
    right: -80px;
    top: -100px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
  }

  .advice-inner {
    position: relative;
    z-index: 1;
    padding: var(--space-6);          /* uniform 24px */
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }
}

.advice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.advice-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-lg);
  font-weight: 600;

  .sparkle {
    background: rgba(255, 255, 255, 0.20);
    border-radius: var(--radius-sm);
    padding: 6px;
    display: inline-flex;
  }

  .cached-tag {
    margin-left: var(--space-1);
    background: rgba(255, 255, 255, 0.16);
    border-color: rgba(255, 255, 255, 0.28);
    color: var(--text-inverse);
  }
}

.refresh-btn {
  color: var(--text-inverse) !important;
  background: rgba(255, 255, 255, 0.14);
  border-radius: var(--radius-sm);
  &:hover { background: rgba(255, 255, 255, 0.22); }
}

.advice-text {
  font-size: var(--fs-lg);
  line-height: 1.6;
  margin: 0;
  font-weight: 500;
}

.advice-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);

  li {
    display: flex;
    align-items: flex-start;
    gap: var(--space-2);
    font-size: var(--fs-base);
    line-height: 1.5;
    opacity: 0.93;

    .bullet {
      background: rgba(255, 255, 255, 0.20);
      border-radius: 50%;
      padding: 3px;
      font-size: var(--fs-xs);
      margin-top: 3px;
      flex-shrink: 0;
    }
  }
}

.advice-foot {
  font-size: var(--fs-sm);
  opacity: 0.68;
}

/* ============================================================
   3. Main grid (calendar + todos)
   ============================================================ */
.main-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-6);
  align-items: start;
}

.calendar-col { position: sticky; top: 0; }

/* Card head — uniform 16px bottom gap */
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--text-primary);

  .count-tag { margin-left: var(--space-2); }
}

/* ============================================================
   4. Mini calendar
   ============================================================ */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--space-1);                /* 4px between day cells */
  margin-bottom: var(--space-4);
}

.cal-day {
  position: relative;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-soft);
  padding: var(--space-1) 2px var(--space-2);
  text-align: center;
  cursor: default;
  transition: background 120ms ease, transform 120ms ease;

  .cal-wd  { font-size: var(--fs-xs); color: var(--text-tertiary); }
  .cal-num { font-size: var(--fs-md); font-weight: 600; color: var(--text-primary); }

  .cal-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: var(--color-primary);
    color: var(--text-inverse);
    border-radius: var(--radius-full);
    font-size: 9px;
    min-width: 15px;
    height: 15px;
    line-height: 15px;
    padding: 0 3px;
  }

  &.has {
    cursor: pointer;
    &:hover {
      background: var(--bg-card);
      transform: translateY(-1px);
      box-shadow: var(--shadow-sm);
    }
  }

  &.today {
    background: var(--color-primary-light);
    border-color: var(--color-primary);
    .cal-num { color: var(--color-primary); }
  }
}

.cal-legend {
  display: flex;
  gap: var(--space-4);

  .dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: var(--space-1);
    vertical-align: middle;
  }

  .dot-today { background: var(--color-primary); }
  .dot-has   { background: var(--color-warning); }
}

/* ============================================================
   5. Todo list — rows separated by hairline
   ============================================================ */
.todo-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.todo-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 120ms ease;

  &:first-child { padding-top: 0; }
  &:last-child  { padding-bottom: 0; border-bottom: none; }

  &.urgent { background: linear-gradient(90deg, rgba(239, 68, 68, 0.05), transparent 70%); }
  &.done .todo-title { color: var(--text-tertiary); text-decoration: line-through; }
}

.todo-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.todo-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.course-chip {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
  white-space: nowrap;
}

.group-name { font-size: var(--fs-sm); }

.todo-title {
  font-size: var(--fs-md);
  font-weight: 500;
  color: var(--text-primary);
  word-break: break-word;
  line-height: 1.4;
}

.todo-sub {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;

  .ddl {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    font-size: var(--fs-sm);
    color: var(--text-secondary);

    .el-icon { font-size: var(--fs-sm); }
    &.is-urgent  { color: var(--color-warning); font-weight: 600; }
    &.is-overdue { color: var(--color-danger);  font-weight: 600; }
  }
}

.todo-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

/* ============================================================
   6. Leader groups — card grid, identical to Groups page
   ============================================================ */
.leader-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
}

.leader-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-6);                /* matches global card-grid */
}

.leader-card {
  cursor: pointer;
  transition: border-color 150ms ease, box-shadow 150ms ease, transform 150ms ease;

  &:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }
}

.leader-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.leader-titles {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;

  .course-chip { align-self: flex-start; }

  .leader-name {
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--text-primary);
    word-break: break-word;
    line-height: 1.35;
  }
}

/* Urgent count badge uses global .badge .badge--danger .badge--pill */

.leader-body {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.ring-wrap { width: 72px; height: 72px; flex-shrink: 0; }

.ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);

  .ring-track {
    fill: none;
    stroke: var(--border-color);
    stroke-width: 5;
  }

  .ring-fill {
    fill: none;
    stroke: var(--color-primary);
    stroke-width: 5;
    stroke-linecap: round;
    transition: stroke-dasharray 400ms ease;
  }

  .ring-text {
    transform: rotate(90deg);
    transform-origin: 32px 32px;
    font-size: 13px;
    font-weight: 700;
    fill: var(--text-primary);
  }
}

.counts {
  flex: 1;
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2) var(--space-4);

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: var(--fs-sm);

    b { font-weight: 600; color: var(--text-primary); }
  }
}

/* ============================================================
   Responsive
   ============================================================ */
@media (max-width: 768px) {
  .main-grid { grid-template-columns: 1fr; }
  .calendar-col { position: static; }
  .advice-text  { font-size: var(--fs-md); }
  .advice-card .advice-bg::after { display: none; }
  .leader-body  { gap: var(--space-3); }
  .ring-wrap    { width: 60px; height: 60px; }
  .todo-actions { flex-direction: column; align-items: stretch; }
}
</style>
