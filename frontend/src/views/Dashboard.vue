<template>
  <div
    class="dashboard page"
    @touchstart.passive="onPullStart"
    @touchend.passive="onPullEnd"
  >
    <div v-if="remoteUpdateHint" class="remote-hint card">
      <span>任务数据有更新</span>
      <button type="button" class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary" @click="applyRemoteUpdate">
        立即刷新
      </button>
    </div>

    <!-- AI 建议（含今日焦点、24h/72h 紧急提醒，整块背景随紧急度变化） -->
    <section
      class="advice-card"
      :class="[
        `advice-card--${adviceCardTone}`,
        { 'is-loading': loading && !advice },
      ]"
    >
      <div class="advice-bg" aria-hidden="true"></div>
      <div class="advice-inner">
        <div class="advice-head">
          <div class="advice-head__title">
            <span class="advice-head__icon" aria-hidden="true">
              <el-icon><MagicStick /></el-icon>
            </span>
            <h2 class="advice-head__label">CoTask AI 建议</h2>
          </div>
          <div class="advice-head__actions">
            <button
              v-if="!loading && focus.critical_count"
              type="button"
              class="insp-capsule-btn insp-capsule-btn--sm advice-action-btn"
              @click="applyUrgencyFilter('critical')"
            >
              处理紧急项
            </button>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--sm advice-action-btn advice-action-btn--primary"
              :disabled="adviceRefreshing"
              @click="refreshAdvicePanel"
            >
              <el-icon><Refresh /></el-icon>
              {{ adviceRefreshLabel }}
            </button>
          </div>
        </div>

        <p v-if="!loading" class="advice-focus">
          <template v-if="focus.open_count">
            今日 {{ focus.open_count }} 项待办
            <template v-if="focus.critical_count">
              · <strong>{{ focus.critical_count }}</strong> 项 24h 内截止
            </template>
            <template v-if="focus.warning_count">
              · <strong>{{ focus.warning_count }}</strong> 项 72h 内
            </template>
          </template>
          <template v-else>今日暂无进行中的任务</template>
        </p>

        <div
          v-if="!loading && urgentCritical.length"
          class="advice-urgent advice-urgent--critical"
        >
          <el-icon class="advice-urgent__icon"><Warning /></el-icon>
          <div class="advice-urgent__text">
            <strong>24 小时内截止 · {{ urgentCritical.length }} 项</strong>
            <span class="advice-urgent__list">
              {{ urgentCritical.slice(0, 3).map((t) => taskDisplayTitle(t)).join('、') }}
              <span v-if="urgentCritical.length > 3"> 等</span>
            </span>
          </div>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm advice-action-btn"
            @click="scrollToTodos"
          >
            查看列表
          </button>
        </div>
        <div
          v-else-if="!loading && urgentWarning.length"
          class="advice-urgent advice-urgent--warning"
        >
          <el-icon class="advice-urgent__icon"><Clock /></el-icon>
          <div class="advice-urgent__text">
            <strong>72 小时内截止 · {{ urgentWarning.length }} 项</strong>
            <span class="advice-urgent__list">{{ urgentWarning.slice(0, 2).map((t) => taskDisplayTitle(t)).join('、') }}</span>
          </div>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm advice-action-btn"
            @click="applyUrgencyFilter('warning')"
          >
            查看
          </button>
        </div>

        <template v-if="loading && !advice">
          <el-skeleton :rows="3" animated class="advice-skeleton" />
        </template>
        <template v-else-if="advice">
          <p class="advice-text">{{ advice.advice }}</p>
          <ul v-if="advice.suggestions?.length" class="advice-list">
            <li v-for="(s, i) in advice.suggestions" :key="i">
              <button
                type="button"
                class="advice-suggestion"
                :disabled="!taskForSuggestion(s)"
                @click="onSuggestionClick(s)"
              >
                <el-icon class="bullet"><Check /></el-icon>
                <span>{{ s }}</span>
              </button>
            </li>
          </ul>
          <div v-if="advice.generated_at" class="advice-foot">
            生成于 {{ relativeTime(advice.generated_at) }}
          </div>
        </template>
        <p v-else-if="!loading" class="advice-empty muted">暂无建议文案，可点击「刷新」生成</p>
      </div>
    </section>

    <!-- Calendar + todos -->
    <div class="main-grid">
      <aside class="calendar-col">
        <div class="dash-panel calendar-card">
          <div class="dash-panel__head">
            <div class="dash-panel__title">
              <span class="dash-panel__icon dash-panel__icon--cal" aria-hidden="true">
                <el-icon><Calendar /></el-icon>
              </span>
              <div class="dash-panel__titles">
                <h3 class="dash-panel__label">月历</h3>
                <p class="dash-panel__sub muted">
                  {{ monthLabel }}
                  <template v-if="monthDdlCount"> · 本月 {{ monthDdlCount }} 个截止</template>
                </p>
              </div>
            </div>
            <div class="cal-nav">
              <button type="button" class="insp-capsule-btn insp-capsule-btn--sm" aria-label="上一月" @click="shiftMonth(-1)">
                <el-icon><ArrowLeft /></el-icon>
              </button>
              <button type="button" class="insp-capsule-btn insp-capsule-btn--sm" aria-label="下一月" @click="shiftMonth(1)">
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
          <div class="month-cal">
            <div class="month-cal__weekdays">
              <span v-for="wd in MONTH_WD_LABELS" :key="wd" class="month-cal__wd">{{ wd }}</span>
            </div>
            <div class="month-cal__grid">
              <button
                v-for="d in monthDays"
                :key="d.iso"
                type="button"
                class="month-cal__day"
                :class="monthDayClass(d)"
                :title="d.ddl?.top ? taskDisplayTitle(d.ddl.top) : undefined"
                :disabled="!d.inMonth && !d.ddl"
                @click="onPickDay(d)"
              >
                <span
                  class="month-cal__num"
                  :class="{
                    'month-cal__num--today': d.isToday,
                    [`month-cal__num--${ddlTone(d)}`]: d.ddl && !d.isToday,
                  }"
                >{{ d.dom }}</span>
                <span class="month-cal__rail" aria-hidden="true">
                  <i
                    v-if="d.ddl"
                    class="month-cal__mark"
                    :class="`month-cal__mark--${ddlTone(d)}`"
                  />
                </span>
              </button>
            </div>
          </div>
          <div class="cal-legend">
            <span class="cal-legend__item"><i class="dot dot-today" />今天</span>
            <span class="cal-legend__item"><i class="dot dot-soon" />72h 内截止</span>
            <span class="cal-legend__item"><i class="dot dot-later" />72h 外截止</span>
          </div>
          <button
            v-if="primaryTimelineGroupId"
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary cal-timeline-link"
            @click="onTimelineGroup(primaryTimelineGroupId)"
          >
            <el-icon><Calendar /></el-icon>
            打开时间轴
          </button>
        </div>
      </aside>

      <section class="todos-col" ref="todosColRef">
        <div class="dash-panel todos-card">
          <div class="dash-panel__head dash-panel__head--stack">
            <div class="dash-panel__title">
              <span class="dash-panel__icon dash-panel__icon--todo" aria-hidden="true">
                <el-icon><List /></el-icon>
              </span>
              <div class="dash-panel__titles">
                <h3 class="dash-panel__label">
                  我的待办
                  <span v-if="!loading" class="dash-count">{{ displayTasks.length }}</span>
                </h3>
                <p class="dash-panel__sub muted">
                  按 DDL 排序
                  <template v-if="selectedDay"> · 已选 {{ selectedDayLabel }}</template>
                </p>
              </div>
            </div>
            <div v-if="selectedDay" class="day-filter-bar">
              <span class="day-filter-bar__text">
                <el-icon><Calendar /></el-icon>
                {{ selectedDayLabel }} 截止
                <strong>{{ displayTasks.length }}</strong> 项
              </span>
              <button type="button" class="insp-capsule-btn insp-capsule-btn--sm" @click="clearDayFilter">
                清除日期
              </button>
            </div>
            <div class="filter-panel">
              <GroupSelect
                v-model="groupFilter"
                :groups="dashFilterGroups"
                variant="dash"
                clearable
                placeholder="全部小组"
              />
              <SegmentedControl v-model="todoFilter" size="sm" :options="todoFilterOptions" />
            </div>
          </div>

          <template v-if="loading">
            <el-skeleton :rows="5" animated />
          </template>
          <template v-else-if="displayTasks.length === 0">
            <el-empty :description="emptyTodoHint" :image-size="100">
              <button
                v-if="selectedDay"
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm"
                @click="selectedDay = null"
              >
                清除日期筛选
              </button>
            </el-empty>
          </template>
          <template v-else>
            <ul class="todo-list">
              <li
                v-for="t in displayTasks"
                :key="`${t.group_id}-${t.task_id}`"
                class="todo-list__item"
                @touchstart.passive="onRowTouchStart(t, $event)"
                @touchend.passive="onRowTouchEnd(t, $event)"
              >
                <TaskNodeCard
                  :node="dashToTaskNode(t)"
                  :members="dashMembers(t)"
                  variant="dashboard"
                  :course-name="t.course_name"
                  :group-name="t.group_name"
                  :course-chip-style="courseChipStyle(t.course_name)"
                  @click="onEnter(t)"
                  @dash-command="(c: string) => onDashCardCommand(t, c)"
                />
              </li>
            </ul>
          </template>
        </div>

        <!-- Unscheduled -->
        <div v-if="!loading && unscheduled.length" class="dash-panel unscheduled-card">
          <div class="dash-panel__head dash-panel__head--compact">
            <div class="dash-panel__title">
              <span class="dash-panel__icon dash-panel__icon--warn" aria-hidden="true">
                <el-icon><Warning /></el-icon>
              </span>
              <div class="dash-panel__titles">
                <h3 class="dash-panel__label">
                  未排期
                  <span class="dash-count dash-count--warn">{{ unscheduled.length }}</span>
                </h3>
                <p class="dash-panel__sub muted">请在项目树中为任务设置截止日期</p>
              </div>
            </div>
          </div>
          <ul class="unscheduled-list">
            <li v-for="t in unscheduled" :key="`u-${t.group_id}-${t.task_id}`" class="unscheduled-item">
              <div class="unscheduled-item__info">
                <span class="course-chip" :style="courseChipStyle(t.course_name)">{{ t.course_name }}</span>
                <span class="unscheduled-item__title">{{ taskDisplayTitle(t) }}</span>
              </div>
              <button type="button" class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary" @click="onEnter(t)">
                去排期
              </button>
            </li>
          </ul>
        </div>
      </section>
    </div>

    <!-- Leader groups -->
    <section v-if="!loading && leaderGroups.length" class="leader-row">
      <div class="dash-section-head">
        <div class="dash-panel__title">
          <span class="dash-panel__icon dash-panel__icon--leader" aria-hidden="true">
            <el-icon><Trophy /></el-icon>
          </span>
          <div class="dash-panel__titles">
            <h3 class="dash-panel__label">我管理的小组</h3>
            <p class="dash-panel__sub muted">进度、紧急项与未指派任务一览</p>
          </div>
        </div>
      </div>
      <div class="leader-grid">
        <article
          v-for="g in leaderGroups"
          :key="g.group_id"
          class="leader-card"
          :style="{ '--leader-accent': courseChipStyle(g.course_name).color }"
        >
          <div class="leader-card__bar" aria-hidden="true" />
          <header class="leader-card__head" @click="onEnterGroup(g.group_id)">
            <div class="leader-card__identity">
              <span class="course-chip" :style="courseChipStyle(g.course_name)">{{ g.course_name }}</span>
              <h4 class="leader-card__name">{{ g.name }}</h4>
            </div>
            <div class="leader-card__badges" :class="{ 'leader-card__badges--empty': !g.urgent_count && !g.unassigned_count }">
              <span v-if="g.urgent_count" class="leader-chip leader-chip--danger">
                <el-icon><Warning /></el-icon>
                紧急 {{ g.urgent_count }}
              </span>
              <span v-if="g.unassigned_count" class="leader-chip">
                未指派 {{ g.unassigned_count }}
              </span>
            </div>
          </header>
          <div class="leader-card__body" @click="onEnterGroup(g.group_id)">
            <div class="leader-ring">
              <svg viewBox="0 0 88 88" class="ring">
                <circle cx="44" cy="44" r="36" class="ring-track" />
                <circle
                  cx="44" cy="44" r="36" class="ring-fill"
                  :stroke-dasharray="`${ringLen(g.progress, 36)} ${ringCirc(36) - ringLen(g.progress, 36)}`"
                />
                <text x="44" y="48" text-anchor="middle" class="ring-text">{{ Math.round(g.progress) }}%</text>
              </svg>
              <span class="leader-ring__caption muted">整体完成度</span>
            </div>
            <div class="leader-stats">
              <div class="leader-stat">
                <b>{{ g.todo }}</b>
                <span class="status-pill status-todo">待办</span>
              </div>
              <div class="leader-stat">
                <b>{{ g.in_progress }}</b>
                <span class="status-pill status-in_progress">进行</span>
              </div>
              <div class="leader-stat">
                <b>{{ g.done }}</b>
                <span class="status-pill status-done">完成</span>
              </div>
              <div class="leader-stat">
                <b>{{ g.blocked }}</b>
                <span class="status-pill status-blocked">阻塞</span>
              </div>
            </div>
          </div>
          <footer class="leader-card__foot">
            <button type="button" class="insp-capsule-btn insp-capsule-btn--sm" @click.stop="onEnterGroup(g.group_id)">
              项目树
            </button>
            <button type="button" class="insp-capsule-btn insp-capsule-btn--sm" @click.stop="onTimelineGroup(g.group_id)">
              时间轴
            </button>
          </footer>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Warning, MagicStick, Refresh, Check, Calendar, List, Clock,
  ArrowLeft, ArrowRight, Trophy,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { calendarDateKey, calendarToday, parseCalendarDate, relativeTime } from '@/utils/datetime'
import {
  Api,
  type AdviceResponse,
  type DashFocus,
  type DashOverviewResponse,
  type DashTask,
  type GroupBrief,
  type LeaderGroup,
  type MemberInfo,
  type TaskNode,
} from '@/api'
import { useWS } from '@/composables/useWS'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import GroupSelect from '@/components/common/GroupSelect.vue'
import TaskNodeCard from '@/components/tree/TaskNodeCard.vue'
import { useGroupsStore } from '@/stores/groups'

const router = useRouter()
const ws = useWS()
const groupsStore = useGroupsStore()

function sortDashTasks(list: DashTask[]): DashTask[] {
  return list.slice().sort((a, b) => {
    const aDone = a.status === 'done' ? 1 : 0
    const bDone = b.status === 'done' ? 1 : 0
    if (aDone !== bDone) return aDone - bDone
    if (aDone) return String(b.end_date || '').localeCompare(String(a.end_date || ''))
    return a.days_left - b.days_left
  })
}

function tasksForGroupFilter(list: DashTask[]): DashTask[] {
  if (!groupFilter.value) return list
  return list.filter((t) => t.group_id === groupFilter.value)
}

const loading = ref(true)
const tasks = ref<DashTask[]>([])
const unscheduled = ref<DashTask[]>([])
const urgentCritical = ref<DashTask[]>([])
const urgentWarning = ref<DashTask[]>([])
const leaderGroups = ref<LeaderGroup[]>([])
const focus = ref<DashFocus>({ open_count: 0, critical_count: 0, warning_count: 0 })

const todoFilter = ref<'open' | 'all'>('open')
const groupFilter = ref<number | null>(null)
const urgencyFilter = ref<'critical' | 'warning' | null>(null)
const selectedDay = ref<string | null>(null)
const monthCursor = ref(calendarToday().startOf('month'))

const doneBusy = reactive<Record<string, boolean>>({})
const advice = ref<AdviceResponse | null>(null)
const adviceLoading = ref(false)
const adviceJobId = ref<number | null>(null)
const todosColRef = ref<HTMLElement | null>(null)
const remoteUpdateHint = ref(false)

const rowTouchX = reactive<Record<string, number>>({})
let pullStartY = 0
let refreshTimer: number | null = null

function applyOverview(data: DashOverviewResponse) {
  tasks.value = sortDashTasks(data.tasks || [])
  unscheduled.value = data.unscheduled || []
  urgentCritical.value = data.urgent || []
  urgentWarning.value = data.urgent_warning || []
  leaderGroups.value = data.leader_groups || []
  focus.value = data.focus || { open_count: 0, critical_count: 0, warning_count: 0 }
  if (data.advice) advice.value = data.advice
}

function scheduleReload() {
  remoteUpdateHint.value = true
  if (refreshTimer) window.clearTimeout(refreshTimer)
  refreshTimer = window.setTimeout(() => {
    refreshTimer = null
    void loadDashboard(false).then(() => {
      remoteUpdateHint.value = false
    })
  }, 800)
}

function applyRemoteUpdate() {
  remoteUpdateHint.value = false
  void loadDashboard(true)
}

async function loadDashboard(showLoad = true) {
  if (showLoad) loading.value = true
  try {
    const data = await Api.dashboardOverview(true)
    applyOverview(data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载首页数据失败')
  } finally {
    loading.value = false
  }
}

async function reloadAll() {
  await loadDashboard(true)
  ElMessage.success('已刷新')
}

const adviceRefreshing = computed(() => loading.value || adviceLoading.value)

const adviceRefreshLabel = computed(() => {
  if (adviceLoading.value) return 'AI 生成中…'
  if (loading.value) return '刷新中…'
  return '刷新'
})

/** Reload dashboard data then regenerate AI advice (single control). */
async function refreshAdvicePanel() {
  if (adviceRefreshing.value) return
  try {
    await loadDashboard(false)
    await refreshAdviceAi()
  } catch {
    /* errors surfaced inside loadDashboard / refreshAdviceAi */
  }
}

function onPullStart(e: TouchEvent) {
  if (window.scrollY <= 8) pullStartY = e.touches[0]?.clientY ?? 0
}

function onPullEnd(e: TouchEvent) {
  if (pullStartY <= 0) return
  const dy = (e.changedTouches[0]?.clientY ?? 0) - pullStartY
  pullStartY = 0
  if (dy > 90 && window.scrollY <= 8) void reloadAll()
}

async function refreshAdviceAi() {
  adviceLoading.value = true
  try {
    const { job_id } = await Api.refreshAdvice()
    adviceJobId.value = job_id
    await pollAdviceJob(job_id)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '无法启动 AI 建议')
    adviceLoading.value = false
  }
}

async function pollAdviceJob(id: number) {
  for (let i = 0; i < 45; i++) {
    await new Promise((r) => setTimeout(r, 2000))
    try {
      const s = await Api.aiJobStatus(id)
      if (s.status === 'done' || s.status === 'completed' || s.status === 'succeeded') {
        if (s.result?.advice) {
          advice.value = {
            advice: s.result.advice,
            suggestions: s.result.suggestions || [],
            generated_at: new Date().toISOString(),
            cached: false,
          }
        } else {
          const data = await Api.dashboardOverview(true)
          if (data.advice) advice.value = data.advice
        }
        adviceLoading.value = false
        adviceJobId.value = null
        ElMessage.success('已刷新')
        return
      }
      if (s.status === 'failed' || s.status === 'error') {
        throw new Error(s.error || '生成失败')
      }
    } catch (e: any) {
      if (e?.response?.status === 404) break
      if (e?.message && !e?.response) {
        adviceLoading.value = false
        adviceJobId.value = null
        ElMessage.error(e.message)
        return
      }
    }
  }
  adviceLoading.value = false
  adviceJobId.value = null
  const data = await Api.dashboardOverview(true)
  if (data.advice) advice.value = data.advice
}

const wsOff: Array<() => void> = []
wsOff.push(ws.on('tree.updated', () => scheduleReload()))
wsOff.push(ws.on('task.status_changed', () => scheduleReload()))
wsOff.push(
  ws.on('ai.job_progress', (data: any) => {
    const id = data?.job_id ?? data?.id
    if (adviceJobId.value && id === adviceJobId.value && data?.status === 'done' && data?.result) {
      advice.value = {
        advice: data.result.advice,
        suggestions: data.result.suggestions || [],
        generated_at: new Date().toISOString(),
        cached: false,
      }
      adviceLoading.value = false
      adviceJobId.value = null
    }
  }),
)

onMounted(() => {
  void loadDashboard()
  if (!groupsStore.loaded) void groupsStore.refresh()
})
onActivated(() => {
  void loadDashboard(false)
})
onUnmounted(() => {
  wsOff.forEach((u) => { try { u() } catch {} })
  if (refreshTimer) window.clearTimeout(refreshTimer)
})

const allOpenTasks = computed(() => [...tasks.value, ...unscheduled.value])

const dashFilterGroups = computed((): GroupBrief[] =>
  [...groupsStore.list]
    .filter((g) => g.status === 'active')
    .sort(
      (a, b) =>
        a.course_name.localeCompare(b.course_name, 'zh') || a.name.localeCompare(b.name, 'zh'),
    ),
)

watch(dashFilterGroups, (groups) => {
  if (groupFilter.value != null && !groups.some((g) => g.id === groupFilter.value)) {
    groupFilter.value = null
  }
})

const openTodoCount = computed(() => {
  const open = tasksForGroupFilter(tasks.value.filter((t) => t.status !== 'done'))
  const unsched = tasksForGroupFilter(unscheduled.value)
  return open.length + unsched.length
})

const allTodoCount = computed(() => {
  return tasksForGroupFilter(tasks.value).length + tasksForGroupFilter(unscheduled.value).length
})

const todoFilterOptions = computed(() => [
  { label: '未完成', value: 'open' as const, badge: openTodoCount.value || undefined },
  { label: '全部', value: 'all' as const, badge: allTodoCount.value || undefined },
])

const baseFiltered = computed(() => {
  let list = todoFilter.value === 'open'
    ? tasks.value.filter((t) => t.status !== 'done')
    : [...tasks.value]
  if (groupFilter.value) list = list.filter((t) => t.group_id === groupFilter.value)
  if (urgencyFilter.value) list = list.filter((t) => t.urgency_level === urgencyFilter.value)
  if (selectedDay.value) {
    list = list.filter(
      (t) => t.end_date && calendarDateKey(t.end_date) === selectedDay.value,
    )
  }
  return list
})

const displayTasks = computed(() => baseFiltered.value)

/** Whole-card background: red when 24h items exist, amber for 72h-only, else calm gradient. */
const adviceCardTone = computed<'critical' | 'warning' | 'default'>(() => {
  if (!loading.value && urgentCritical.value.length) return 'critical'
  if (!loading.value && urgentWarning.value.length) return 'warning'
  return 'default'
})

const emptyTodoHint = computed(() => {
  if (selectedDay.value) return '该日没有截止的任务'
  if (urgencyFilter.value || groupFilter.value) {
    return '没有符合筛选条件的任务'
  }
  if (todoFilter.value === 'open' && tasks.value.some((t) => t.status === 'done')) {
    return '暂无未完成任务，可切换「全部」查看已完成'
  }
  if (todoFilter.value === 'all') return '暂无任务'
  return '暂无待办，去看看时间轴或项目树吧'
})

const primaryTimelineGroupId = computed(() => {
  if (urgentCritical.value.length) return urgentCritical.value[0].group_id
  if (tasks.value.length) return tasks.value[0].group_id
  if (leaderGroups.value.length) return leaderGroups.value[0].group_id
  return null
})

function applyUrgencyFilter(level: 'critical' | 'warning') {
  urgencyFilter.value = level
  selectedDay.value = null
  scrollToTodos()
}

interface DayDdlInfo {
  count: number
  /** DDL within 72h (critical + warning from API). */
  soon: number
  /** DDL more than 72h away. */
  later: number
  top?: DashTask
}

interface MonthDay {
  iso: string
  dom: number
  inMonth: boolean
  isToday: boolean
  ddl: DayDdlInfo | null
}

const MONTH_WD_LABELS = ['一', '二', '三', '四', '五', '六', '日']

const ddlByDay = computed(() => {
  const map: Record<string, DayDdlInfo> = {}
  for (const t of tasks.value) {
    if (!t.end_date) continue
    const key = calendarDateKey(t.end_date)
    if (!map[key]) map[key] = { count: 0, soon: 0, later: 0 }
    const slot = map[key]
    slot.count += 1
    if (t.urgency_level === 'critical' || t.urgency_level === 'warning') {
      slot.soon += 1
    } else {
      slot.later += 1
    }
    if (!slot.top || t.days_left < slot.top.days_left) slot.top = t
  }
  return map
})

const monthLabel = computed(() => monthCursor.value.format('YYYY年 M月'))

const monthDays = computed<MonthDay[]>(() => {
  const monthStart = monthCursor.value.startOf('month')
  const daysInMonth = monthCursor.value.daysInMonth()
  const pad = (monthStart.day() + 6) % 7 // Monday-first leading cells
  const gridStart = monthStart.subtract(pad, 'day').startOf('day')
  const weekRows = Math.ceil((pad + daysInMonth) / 7)
  const totalCells = weekRows * 7
  const today = calendarToday()
  const monthIdx = monthCursor.value.month()
  const days: MonthDay[] = []
  for (let i = 0; i < totalCells; i++) {
    const d = gridStart.add(i, 'day').startOf('day')
    const iso = d.format('YYYY-MM-DD')
    const slot = ddlByDay.value[iso]
    days.push({
      iso,
      dom: d.date(),
      inMonth: d.month() === monthIdx,
      isToday: d.isSame(today, 'day'),
      ddl: slot?.count ? slot : null,
    })
  }
  return days
})

const monthDdlCount = computed(() => {
  const prefix = monthCursor.value.format('YYYY-MM')
  return Object.entries(ddlByDay.value)
    .filter(([iso]) => iso.startsWith(prefix))
    .reduce((sum, [, v]) => sum + v.count, 0)
})

const selectedDayLabel = computed(() =>
  selectedDay.value ? parseCalendarDate(selectedDay.value).format('M月D日') : '',
)

function shiftMonth(delta: number) {
  monthCursor.value = monthCursor.value.add(delta, 'month').startOf('month')
}

function clearDayFilter() {
  selectedDay.value = null
}

function ddlTone(d: MonthDay): 'soon' | 'later' {
  if (!d.ddl) return 'later'
  return d.ddl.soon > 0 ? 'soon' : 'later'
}

function monthDayClass(d: MonthDay) {
  const tone = d.ddl ? ddlTone(d) : null
  return {
    'month-cal__day--off': !d.inMonth,
    'month-cal__day--today': d.isToday,
    'month-cal__day--ddl': !!d.ddl,
    'month-cal__day--soon': tone === 'soon',
    'month-cal__day--later': tone === 'later',
    'month-cal__day--selected': selectedDay.value === d.iso,
  }
}

function onPickDay(d: MonthDay) {
  if (!d.ddl?.count) {
    if (selectedDay.value === d.iso) {
      selectedDay.value = null
      return
    }
    if (d.inMonth) ElMessage.info('该日没有截止任务')
    return
  }
  if (!d.inMonth) {
    monthCursor.value = parseCalendarDate(d.iso).startOf('month')
  }
  const next = selectedDay.value === d.iso ? null : d.iso
  selectedDay.value = next
  if (next) scrollToTodos()
}

function taskDisplayTitle(t: DashTask): string {
  return (t.title_path && t.title_path.trim()) || t.title
}

function taskForSuggestion(s: string): DashTask | undefined {
  const m = s.match(/「([^」]+)」/)
  if (!m) return undefined
  const q = m[1]
  return allOpenTasks.value.find((t) => {
    const full = taskDisplayTitle(t)
    return full === q || t.title === q || full.includes(q) || q.includes(full) || t.title.includes(q)
  })
}

function onSuggestionClick(s: string) {
  const t = taskForSuggestion(s)
  if (t) onEnter(t)
}

function dashToTaskNode(t: DashTask): TaskNode {
  return {
    id: t.task_id,
    parent_id: null,
    title: taskDisplayTitle(t),
    description: '',
    is_leaf: !t.has_children,
    refined: false,
    start_date: t.start_date ?? undefined,
    end_date: t.end_date ?? undefined,
    status: t.status as TaskNode['status'],
    progress: t.progress,
    depth: 0,
    position: 0,
    path: '',
    assignees: (t.assignees || []).map((a) => a.user_id),
    dependencies: [],
    version: 0,
  }
}

function dashMembers(t: DashTask): MemberInfo[] {
  return (t.assignees || []).map((a) => ({
    user_id: a.user_id,
    name: a.name,
    avatar_url: a.avatar_url ?? undefined,
    role: 'member',
    joined_at: '',
    contribution: 0,
    skills: [],
  }))
}

function onDashCardCommand(t: DashTask, cmd: string) {
  if (cmd === 'timeline') onTimeline(t)
  else if (cmd === 'done') void onMarkDone(t)
  else if (cmd === 'todo' || cmd === 'in_progress' || cmd === 'blocked') void onStatus(t, cmd)
}

const palette = [
  { bg: 'rgba(61,126,255,0.12)', fg: '#1D4ED8' },
  { bg: 'rgba(245,108,108,0.12)', fg: '#B91C1C' },
  { bg: 'rgba(103,194,58,0.14)', fg: '#15803D' },
  { bg: 'rgba(230,162,60,0.14)', fg: '#B45309' },
  { bg: 'rgba(159,122,234,0.14)', fg: '#6D28D9' },
  { bg: 'rgba(20,184,166,0.14)', fg: '#0F766E' },
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

function busyKey(t: DashTask) {
  return `${t.group_id}-${t.task_id}`
}

async function onMarkDone(t: DashTask) {
  const key = busyKey(t)
  doneBusy[key] = true
  try {
    await Api.changeStatus(t.group_id, t.task_id, 'done')
    t.status = 'done'
    urgentCritical.value = urgentCritical.value.filter((u) => u.task_id !== t.task_id)
    urgentWarning.value = urgentWarning.value.filter((u) => u.task_id !== t.task_id)
    await loadDashboard(false)
    ElMessage.success('任务已完成')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '更新失败')
  } finally {
    doneBusy[key] = false
  }
}

async function onStatus(t: DashTask, status: string) {
  const key = busyKey(t)
  doneBusy[key] = true
  try {
    await Api.changeStatus(t.group_id, t.task_id, status)
    t.status = status as DashTask['status']
    await loadDashboard(false)
    ElMessage.success('状态已更新')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '更新失败')
  } finally {
    doneBusy[key] = false
  }
}

function onEnter(t: DashTask) {
  router.push({ path: `/groups/${t.group_id}/tree`, query: { select: String(t.task_id) } })
}
function onTimeline(t: DashTask) {
  router.push(`/groups/${t.group_id}/timeline`)
}
function onEnterGroup(gid: number) {
  router.push(`/groups/${gid}/tree`)
}
function onTimelineGroup(gid: number) {
  router.push(`/groups/${gid}/timeline`)
}

function onRowTouchStart(t: DashTask, e: TouchEvent) {
  rowTouchX[busyKey(t)] = e.touches[0]?.clientX ?? 0
}

function onRowTouchEnd(t: DashTask, e: TouchEvent) {
  const start = rowTouchX[busyKey(t)]
  if (start == null) return
  const dx = (e.changedTouches[0]?.clientX ?? 0) - start
  if (dx > 72 && !t.has_children && t.status !== 'done') void onMarkDone(t)
  delete rowTouchX[busyKey(t)]
}

function scrollToTodos() {
  todosColRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function ringCirc(radius: number) {
  return 2 * Math.PI * radius
}
function ringLen(progress: number, radius = 36) {
  return (Math.max(0, Math.min(100, progress)) / 100) * ringCirc(radius)
}
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.advice-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  color: var(--text-inverse);
  box-shadow: var(--shadow-md);

  .advice-bg {
    position: absolute;
    inset: 0;
    transition: background 280ms ease;
  }

  &.advice-card--default .advice-bg {
    background: linear-gradient(135deg, #0d9488 0%, #2563eb 48%, #4f46e5 100%);
  }

  &.advice-card--critical .advice-bg {
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 42%, #ea580c 100%);
  }

  &.advice-card--warning .advice-bg {
    background: linear-gradient(135deg, #78350f 0%, #d97706 50%, #ca8a04 100%);
  }

  .advice-bg::after {
    content: '';
    position: absolute;
    width: 280px;
    height: 280px;
    right: -60px;
    top: -80px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
  }

  .advice-inner {
    position: relative;
    z-index: 1;
    padding: var(--space-5) var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }
}

.advice-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.advice-head__title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.advice-head__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.18);

  .el-icon { font-size: 18px; }
}

.advice-head__label {
  margin: 0;
  font-size: var(--fs-lg);
  font-weight: 600;
  line-height: 1.3;
}

.advice-head__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: flex-end;
}

.advice-action-btn {
  background: rgba(255, 255, 255, 0.12) !important;
  border-color: rgba(255, 255, 255, 0.28) !important;
  color: #fff !important;

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2) !important;
    color: #fff !important;
  }

  &--primary {
    background: rgba(255, 255, 255, 0.95) !important;
    border-color: transparent !important;
    color: #3730a3 !important;
    font-weight: 600;

    &:hover:not(:disabled) {
      background: #fff !important;
      color: #312e81 !important;
    }
  }
}

.advice-focus {
  margin: 0;
  font-size: var(--fs-sm);
  line-height: 1.5;
  opacity: 0.92;

  strong { font-weight: 700; }
}

.advice-urgent {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(6px);

  &__icon {
    font-size: 22px;
    flex-shrink: 0;
    opacity: 0.95;
  }

  &__text {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    font-size: var(--fs-sm);
    line-height: 1.45;

    strong { font-size: var(--fs-sm); font-weight: 700; }
  }

  &__list {
    opacity: 0.9;
    font-size: var(--fs-xs);
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
}

.advice-skeleton :deep(.el-skeleton__item) {
  background: rgba(255, 255, 255, 0.15);
}

.advice-text {
  margin: 0;
  font-size: var(--fs-md);
  line-height: 1.6;
  font-weight: 500;
}

.advice-empty {
  margin: 0;
  font-size: var(--fs-sm);
}
.advice-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.advice-suggestion {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  text-align: left;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font: inherit;
  padding: 0;
  opacity: 0.95;
  &:disabled { cursor: default; opacity: 0.85; }
  &:not(:disabled):hover { text-decoration: underline; }
  .bullet { flex-shrink: 0; margin-top: 3px; }
}
.advice-foot { font-size: var(--fs-xs); opacity: 0.7; }

.dashboard.page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* Shared dashboard panels */
.dash-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  box-shadow: var(--shadow-sm);
}

.dash-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;

  &--stack {
    flex-direction: column;
    align-items: stretch;
  }

  &--compact {
    margin-bottom: var(--space-4);
  }
}

.dash-panel__title {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-width: 0;
}

.dash-panel__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;

  &--cal {
    background: color-mix(in srgb, var(--color-primary) 14%, var(--bg-soft));
    color: var(--color-primary);
  }
  &--todo {
    background: color-mix(in srgb, #6366f1 14%, var(--bg-soft));
    color: #4f46e5;
  }
  &--warn {
    background: color-mix(in srgb, var(--color-warning) 18%, var(--bg-soft));
    color: var(--color-warning);
  }
  &--leader {
    background: color-mix(in srgb, #d97706 16%, var(--bg-soft));
    color: #b45309;
  }
}

.dash-panel__label {
  margin: 0;
  font-size: var(--fs-md);
  font-weight: 600;
  line-height: 1.35;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.dash-panel__sub {
  margin: var(--space-1) 0 0;
  font-size: var(--fs-xs);
  line-height: 1.4;
}

.dash-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.35rem;
  padding: 0 var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: 700;
  background: var(--color-primary-light);
  color: var(--color-primary);

  &--warn {
    background: color-mix(in srgb, var(--color-warning) 20%, transparent);
    color: var(--color-warning);
  }
}

.dash-section-head {
  margin-bottom: var(--space-2);
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(300px, 340px) 1fr;
  gap: var(--space-6);
  align-items: start;
}
.calendar-col { position: sticky; top: var(--space-4); }

.filter-panel {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.day-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-primary) 10%, var(--bg-soft));
  border: 1px solid color-mix(in srgb, var(--color-primary) 28%, var(--border-subtle));

  &__text {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--fs-sm);
    color: var(--text-secondary);

    strong {
      color: var(--color-primary);
      font-weight: 700;
    }
  }
}

.cal-nav {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.month-cal {
  margin-bottom: var(--space-3);

  &__weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
    margin-bottom: 4px;
    padding: 0 1px;
  }

  &__wd {
    text-align: center;
    font-size: 10px;
    font-weight: 600;
    color: var(--text-tertiary);
    line-height: 1;
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
    row-gap: 2px;
  }

  &__day {
    position: relative;
    display: grid;
    grid-template-rows: 24px 8px;
    align-items: center;
    justify-items: center;
    height: 34px;
    padding: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    cursor: default;
    font: inherit;
    color: inherit;

    &:not(:disabled):hover .month-cal__num:not(.month-cal__num--today) {
      background: var(--bg-soft);
    }

    &--off {
      opacity: 0.35;

      .month-cal__num {
        color: var(--text-tertiary);
        font-weight: 500;
      }

      &.month-cal__day--ddl {
        opacity: 0.6;
        cursor: pointer;
      }
    }

    &--ddl:not(:disabled) {
      cursor: pointer;
    }

    &--selected .month-cal__num {
      box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 45%, transparent);
      background: var(--color-primary-light);
      color: var(--color-primary);
      font-weight: 700;
    }

    &--selected.month-cal__day--today .month-cal__num {
      box-shadow: 0 0 0 2px #fff, 0 0 0 4px var(--color-primary);
    }
  }

  &__num {
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
    color: var(--text-primary);
    border-radius: var(--radius-full);
    transition: background 120ms ease, color 120ms ease, box-shadow 120ms ease;

    &--today {
      color: #fff;
      font-weight: 700;
      background: var(--color-primary);
    }

    &--soon {
      color: var(--color-danger);
      font-weight: 700;
    }

    &--later {
      color: color-mix(in srgb, var(--color-primary) 88%, var(--text-primary));
      font-weight: 600;
    }
  }

  &__rail {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 8px;
    width: 100%;
  }

  &__mark {
    display: block;
    width: 14px;
    height: 2px;
    border-radius: var(--radius-full);
    flex-shrink: 0;

    &--soon {
      background: var(--color-danger);
    }

    &--later {
      background: color-mix(in srgb, var(--color-primary) 55%, var(--border-color));
    }
  }
}

.cal-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  margin-bottom: var(--space-3);
  font-size: 10px;
  line-height: 1.2;
  color: var(--text-secondary);

  &__item {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
  }

  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .dot-today { background: var(--color-primary); }
  .dot-soon { background: var(--color-danger); }
  .dot-later {
    background: color-mix(in srgb, var(--color-primary) 55%, var(--border-color));
  }
}

.todos-col { display: flex; flex-direction: column; gap: var(--space-6); }

.todo-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.todo-list__item {
  list-style: none;
}

.course-chip {
  font-size: var(--fs-xs);
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-weight: 600;
  line-height: 1.3;
}
.remote-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-primary);
  background: var(--color-primary-light);
  font-size: var(--fs-sm);
}

.cal-timeline-link {
  width: 100%;
}

.unscheduled-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.unscheduled-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px dashed color-mix(in srgb, var(--color-warning) 45%, var(--border-color));
  background: color-mix(in srgb, var(--color-warning) 5%, var(--bg-soft));

  &__info {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
  }

  &__title {
    font-size: var(--fs-sm);
    font-weight: 500;
    word-break: break-word;
  }
}

.leader-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.leader-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  align-items: stretch;
  gap: var(--space-6);
}

.leader-card {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
  padding: 0;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow 180ms ease, border-color 180ms ease, transform 180ms ease;

  &:hover {
    border-color: color-mix(in srgb, var(--leader-accent, var(--color-primary)) 50%, var(--border-color));
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  &__bar {
    height: 4px;
    background: linear-gradient(
      90deg,
      var(--leader-accent, var(--color-primary)),
      color-mix(in srgb, var(--leader-accent, var(--color-primary)) 40%, transparent)
    );
  }

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
    flex-shrink: 0;
    min-height: 88px;
    padding: var(--space-4) var(--space-5) var(--space-3);
    cursor: pointer;
  }

  &__identity {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    min-width: 0;
  }

  &__name {
    margin: 0;
    font-size: var(--fs-md);
    font-weight: 600;
    line-height: 1.35;
    word-break: break-word;
  }

  &__badges {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    justify-content: flex-start;
    gap: var(--space-1);
    flex-shrink: 0;
    min-width: 88px;
    min-height: 52px;

    &--empty {
      visibility: hidden;
      pointer-events: none;
    }
  }

  &__body {
    display: flex;
    align-items: flex-start;
    flex: 1;
    gap: var(--space-5);
    padding: 0 var(--space-5) var(--space-4);
    cursor: pointer;
  }

  &__foot {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-start;
    flex-shrink: 0;
    gap: var(--space-2);
    margin-top: auto;
    padding: var(--space-3) var(--space-5) var(--space-4);
    border-top: 1px solid var(--border-subtle);
    background: var(--bg-soft);
  }
}

.leader-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  font-size: var(--fs-xs);
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  background: var(--bg-soft);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  white-space: nowrap;

  &--danger {
    background: color-mix(in srgb, var(--color-danger) 12%, var(--bg-card));
    color: var(--color-danger);
    border-color: color-mix(in srgb, var(--color-danger) 25%, transparent);
  }
}

.leader-ring {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  width: 96px;

  .ring {
    width: 88px;
    height: 88px;
    transform: rotate(-90deg);
  }

  .ring-track {
    fill: none;
    stroke: var(--border-color);
    stroke-width: 6;
  }

  .ring-fill {
    fill: none;
    stroke: var(--leader-accent, var(--color-primary));
    stroke-width: 6;
    stroke-linecap: round;
  }

  .ring-text {
    transform: rotate(90deg);
    transform-origin: 44px 44px;
    font-size: 15px;
    font-weight: 700;
    fill: var(--text-primary);
  }

  &__caption {
    font-size: 10px;
    text-align: center;
  }
}

.leader-stats {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.leader-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--bg-soft);
  border: 1px solid var(--border-subtle);

  b {
    font-size: var(--fs-lg);
    font-weight: 700;
    line-height: 1;
    color: var(--text-primary);
  }

  .status-pill {
    font-size: 10px;
    padding: 2px 6px;
  }
}

@media (max-width: 900px) {
  .advice-head { flex-direction: column; align-items: stretch; }
  .advice-head__actions { justify-content: flex-start; }
  .main-grid { grid-template-columns: 1fr; }
  .calendar-col { position: static; }
  .leader-card__body {
    flex-direction: column;
    align-items: stretch;
  }

  .leader-ring {
    width: 100%;
    flex-direction: row;
    justify-content: center;
  }

}

html.dark {
  .advice-card--default .advice-bg {
    background: linear-gradient(135deg, #115e59 0%, #1e3a8a 50%, #312e81 100%);
  }
  .advice-card--critical .advice-bg {
    background: linear-gradient(135deg, #450a0a 0%, #991b1b 45%, #c2410c 100%);
  }
  .advice-card--warning .advice-bg {
    background: linear-gradient(135deg, #451a03 0%, #b45309 50%, #a16207 100%);
  }
  .advice-urgent {
    background: rgba(0, 0, 0, 0.28);
    border-color: rgba(255, 255, 255, 0.14);
  }
  .remote-hint {
    background: color-mix(in srgb, var(--color-primary) 18%, var(--bg-card));
  }
  .dash-panel {
    box-shadow: none;
  }

  .dash-panel__icon--todo {
    color: #a5b4fc;
  }

  .day-filter-bar {
    background: color-mix(in srgb, var(--color-primary) 16%, var(--bg-soft));
  }

  .leader-card__foot {
    background: color-mix(in srgb, var(--bg-soft) 70%, #000);
  }

  .leader-stat {
    background: color-mix(in srgb, var(--bg-soft) 60%, #000);
  }
}
</style>
