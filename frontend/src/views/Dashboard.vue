<template>
  <div class="dashboard">
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
            <el-radio-group
              v-model="todoFilter"
              size="small"
            >
              <el-radio-button label="open">未完成</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
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
              class="urgent-badge"
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

const router = useRouter()

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
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* urgent banner */
.urgent-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);

  .ub-icon { font-size: 20px; }
  .ub-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    .ub-list { font-size: 13px; opacity: 0.9; }
  }
}

/* AI advice */
.advice-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  color: #fff;
  box-shadow: var(--shadow-card);

  .advice-bg {
    position: absolute; inset: 0;
    background: linear-gradient(135deg, #3D7EFF 0%, #6F4DFF 60%, #9B5BFF 100%);
    z-index: 0;
  }
  .advice-bg::after {
    content: '';
    position: absolute;
    width: 240px; height: 240px;
    right: -60px; top: -80px;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 50%;
  }
  .advice-inner {
    position: relative;
    z-index: 1;
    padding: 20px 22px;
  }
}
.advice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.advice-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  .sparkle {
    background: rgba(255, 255, 255, 0.22);
    border-radius: 8px;
    padding: 6px;
  }
  .cached-tag {
    margin-left: 4px;
    background: rgba(255,255,255,0.18);
    border-color: rgba(255,255,255,0.32);
    color: #fff;
  }
}
.refresh-btn {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.14);
  &:hover { background: rgba(255, 255, 255, 0.24); }
}
.advice-text {
  font-size: 17px;
  line-height: 1.55;
  margin: 0 0 12px 0;
  font-weight: 500;
}
.advice-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  li {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 14px;
    line-height: 1.5;
    opacity: 0.95;
    .bullet {
      background: rgba(255,255,255,0.22);
      border-radius: 50%;
      padding: 3px;
      font-size: 12px;
      margin-top: 3px;
      flex-shrink: 0;
    }
  }
}
.advice-foot {
  margin-top: 12px;
  font-size: 12px;
  opacity: 0.7;
}

/* main grid */
.main-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: start;
}
.calendar-col {
  position: sticky;
  top: 0;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  .count-tag { margin-left: 6px; }
}

/* calendar */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 12px;
}
.cal-day {
  position: relative;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-soft);
  padding: 6px 4px 8px;
  text-align: center;
  cursor: default;
  transition: background .15s, transform .15s;

  .cal-wd { font-size: 11px; color: var(--text-tertiary); }
  .cal-num { font-size: 16px; font-weight: 600; color: var(--text-primary); }
  .cal-badge {
    position: absolute;
    top: 2px; right: 2px;
    background: var(--color-primary);
    color: #fff;
    border-radius: 999px;
    font-size: 10px;
    min-width: 16px;
    height: 16px;
    line-height: 16px;
    padding: 0 4px;
  }
  &.has { cursor: pointer; }
  &.has:hover {
    background: var(--bg-card);
    transform: translateY(-1px);
  }
  &.today {
    background: rgba(61,126,255,0.1);
    border-color: var(--color-primary);
    .cal-num { color: var(--color-primary); }
  }
}
.cal-legend {
  display: flex;
  gap: 12px;
  .dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
  }
  .dot-today { background: var(--color-primary); }
  .dot-has   { background: var(--color-accent); }
}

/* todos */
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
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border-color);
  &:last-child { border-bottom: none; }

  &.urgent { background: linear-gradient(90deg, rgba(245,108,108,0.06), transparent 60%); }
  &.done .todo-title { color: var(--text-tertiary); text-decoration: line-through; }
}
.todo-main {
  flex: 1;
  min-width: 0;
}
.todo-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.course-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
  white-space: nowrap;
}
.group-name { font-size: 12px; }
.todo-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  word-break: break-word;
}
.todo-sub {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;

  .ddl {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--text-secondary);
    .el-icon { font-size: 12px; }
    &.is-urgent  { color: var(--color-warning); font-weight: 600; }
    &.is-overdue { color: var(--color-danger);  font-weight: 600; }
  }
}
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 999px;
}
.todo-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* leader cards */
.leader-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.leader-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.leader-card {
  cursor: pointer;
  transition: transform .15s, box-shadow .15s;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
  }
}
.leader-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
.leader-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;

  .course-chip { align-self: flex-start; }
  .leader-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    word-break: break-word;
  }
}
.urgent-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(245,108,108,0.14);
  color: var(--color-danger);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.leader-body {
  display: flex;
  align-items: center;
  gap: 16px;
}
.ring-wrap { width: 72px; height: 72px; flex-shrink: 0; }
.ring {
  width: 100%; height: 100%;
  transform: rotate(-90deg);
  .ring-track {
    fill: none;
    stroke: var(--border-color);
    stroke-width: 6;
  }
  .ring-fill {
    fill: none;
    stroke: var(--color-primary);
    stroke-width: 6;
    stroke-linecap: round;
    transition: stroke-dasharray .4s ease;
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
  gap: 6px 12px;

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    b { font-weight: 600; color: var(--text-primary); }
  }
}

/* responsive */
@media (max-width: 768px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  .calendar-col { position: static; }
  .advice-text { font-size: 15px; }
  .advice-card .advice-bg::after { display: none; }
  .leader-body { gap: 12px; }
  .ring-wrap { width: 60px; height: 60px; }
  .todo-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
