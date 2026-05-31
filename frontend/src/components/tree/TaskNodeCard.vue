<template>
  <div
    class="tnc"
    :class="{
      'is-selected': selected,
      'is-overdue': isOverdue,
      'tnc--dashboard': variant === 'dashboard',
    }"
    @click="onClick"
  >
    <span class="status-dot" :class="`dot-${node.status}`" :title="statusLabel"></span>

    <div class="tnc-main">
      <div v-if="courseName || groupName" class="tnc-attr-row">
        <span v-if="courseName" class="course-chip" :style="courseChipStyle">{{ courseName }}</span>
        <span v-if="groupName" class="tnc-group muted">{{ groupName }}</span>
      </div>
      <div class="tnc-title-row">
        <span class="tnc-title">{{ node.title }}</span>
        <span v-if="node.refined" class="chip chip-refined" title="已细化">已细化</span>
      </div>
      <div v-if="node.description" class="tnc-desc muted">
        {{ singleLine(node.description) }}
      </div>
    </div>

    <div
      class="tnc-right tnc-right--grid"
      :class="{ 'tnc-right--dash': variant === 'dashboard' }"
    >
      <div class="tnc-col tnc-col--assignees">
        <div class="assignees">
          <template v-if="assigneeMembers.length">
            <el-tooltip
              v-for="m in assigneeMembers.slice(0, 3)"
              :key="m.user_id"
              :content="m.name"
              placement="top"
            >
              <el-avatar :size="24" :src="avatarSrc(m)" class="av">
                <template v-if="!avatarSrc(m)">{{ (m.name || '?').slice(0, 1) }}</template>
              </el-avatar>
            </el-tooltip>
            <span v-if="assigneeMembers.length > 3" class="av-more">+{{ assigneeMembers.length - 3 }}</span>
          </template>
          <span v-else class="av-empty tiny muted">未指派</span>
        </div>
      </div>

      <div class="tnc-col tnc-col--ddl">
        <div v-if="node.end_date" class="ddl-pill" :class="ddlClass">
          <el-icon><Clock /></el-icon>
          <span>{{ ddlLabel }}</span>
        </div>
        <span v-else class="tnc-ddl-empty muted">—</span>
      </div>

      <div class="tnc-col tnc-col--progress">
        <div class="progress-wrap" :title="progressTitle">
          <div class="progress-bar">
            <div
              class="progress-fill"
              :class="progressFillClass"
              :style="progressFillStyle"
            />
          </div>
        </div>
      </div>

      <div v-if="variant === 'dashboard'" class="tnc-col tnc-col--status">
        <el-dropdown
          v-if="node.is_leaf"
          trigger="click"
          @command="onStatusCmd"
          @click.stop
        >
          <el-button
            size="small"
            text
            class="tnc-status-btn"
            :class="`tnc-status-btn--${node.status}`"
            @click.stop
          >
            {{ statusLabel }}
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="opt in statusOptions"
                :key="opt.value"
                :command="opt.value"
                :disabled="node.status === opt.value"
              >
                {{ opt.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <span
          v-else
          class="tnc-status-readonly muted"
          title="状态由子任务汇总"
        >
          {{ statusLabel }}
        </span>
      </div>

      <div class="tnc-col tnc-col--actions">
        <div class="tnc-actions">
          <el-button size="small" text @click.stop="onClick">详情</el-button>
          <el-dropdown trigger="click" @command="onCmd" @click.stop>
            <el-button size="small" text class="tnc-more-btn" @click.stop>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu v-if="variant === 'dashboard'">
                <el-dropdown-item command="detail">查看详情</el-dropdown-item>
                <el-dropdown-item command="timeline">时间轴</el-dropdown-item>
              </el-dropdown-menu>
              <el-dropdown-menu v-else>
                <el-dropdown-item command="detail">查看详情</el-dropdown-item>
                <el-dropdown-item
                  v-if="canEdit"
                  command="add-child"
                >添加子任务</el-dropdown-item>
                <el-dropdown-item
                  v-if="canEdit"
                  divided
                  command="delete"
                  style="color: var(--color-danger)"
                >删除节点</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'
import { ArrowDown, Clock, MoreFilled } from '@element-plus/icons-vue'
import type { TaskNode, MemberInfo } from '@/api'
import { taskBarPercent } from '@/utils/taskProgress'

const props = withDefaults(
  defineProps<{
    node: TaskNode
    members: MemberInfo[]
    selected?: boolean
    canEdit?: boolean
    variant?: 'tree' | 'dashboard'
    courseName?: string
    groupName?: string
    courseChipStyle?: Record<string, string>
  }>(),
  { variant: 'tree' },
)

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'add-child'): void
  (e: 'delete'): void
  (e: 'dash-command', cmd: string): void
}>()

const memberMap = computed(() => {
  const m = new Map<number, MemberInfo>()
  for (const x of props.members) m.set(x.user_id, x)
  return m
})

const assigneeMembers = computed(() =>
  (props.node.assignees || [])
    .map((id) => memberMap.value.get(id))
    .filter(Boolean) as MemberInfo[],
)

const barPct = computed(() => taskBarPercent(props.node))

/** done = 本任务完成，或后端已按子任务汇总为完成 */
const progressFillClass = computed(() => {
  if (props.node.status === 'blocked') return 'progress-fill--blocked'
  if (props.node.status === 'done') return 'progress-fill--done'
  return 'progress-fill--active'
})

const progressFillStyle = computed(() => {
  if (props.node.status === 'blocked' || props.node.status === 'done') {
    return { width: '100%' }
  }
  return { width: barPct.value > 0 ? `${barPct.value}%` : '0%' }
})

const progressTitle = computed(() => {
  if (props.node.status === 'blocked') return '已阻塞'
  if (props.node.status === 'done') return '已完成'
  if (props.node.status === 'in_progress') return '进行中'
  return '待办'
})

const statusLabel = computed(() =>
  ({ todo: '待办', in_progress: '进行中', done: '已完成', blocked: '已阻塞' } as Record<string, string>)[
    props.node.status
  ] || props.node.status,
)

const statusOptions = [
  { value: 'todo', label: '待办' },
  { value: 'in_progress', label: '进行中' },
  { value: 'blocked', label: '已阻塞' },
  { value: 'done', label: '已完成' },
] as const

const daysLeft = computed(() => {
  if (!props.node.end_date) return null
  const end = dayjs(props.node.end_date).endOf('day')
  return end.diff(dayjs(), 'hour') / 24
})

const isOverdue = computed(
  () => daysLeft.value !== null && daysLeft.value < 0 && props.node.status !== 'done',
)
const isWarn = computed(
  () =>
    daysLeft.value !== null &&
    daysLeft.value >= 0 &&
    daysLeft.value <= 3 &&
    props.node.status !== 'done',
)

const ddlClass = computed(() => {
  if (props.node.status === 'done') return 'ddl-done'
  if (isOverdue.value) return 'ddl-overdue'
  if (isWarn.value) return 'ddl-warn'
  return 'ddl-default'
})

const ddlLabel = computed(() => {
  if (!props.node.end_date) return ''
  const d = daysLeft.value!
  if (d < 0) return `逾期 ${Math.ceil(-d)} 天`
  if (d < 1) return '今天'
  if (d < 2) return '明天'
  if (d < 7) return `${Math.ceil(d)} 天`
  return dayjs(props.node.end_date).format('MM-DD')
})

function singleLine(s: string) {
  return (s || '').replace(/\s+/g, ' ').trim()
}

function avatarSrc(m: MemberInfo): string | undefined {
  const url = m.avatar_url?.trim()
  return url || undefined
}

function onClick() {
  emit('click')
}

function onStatusCmd(c: string) {
  if (props.variant === 'dashboard' && props.node.is_leaf) {
    emit('dash-command', c)
  }
}

function onCmd(c: string) {
  if (props.variant === 'dashboard') {
    if (c === 'detail') emit('click')
    else emit('dash-command', c)
    return
  }
  if (c === 'detail') emit('click')
  else if (c === 'add-child') emit('add-child')
  else if (c === 'delete') emit('delete')
}
</script>

<style lang="scss" scoped>
.tnc {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: transform .12s, box-shadow .12s, border-color .12s;
  min-height: 56px;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    border-color: var(--color-primary);
    .tnc-actions { opacity: 1; }
  }
  &.is-selected {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(61,126,255,0.18);
  }

  &.is-overdue {
    background: color-mix(in srgb, var(--color-danger) 8%, var(--bg-card));
    border-color: color-mix(in srgb, var(--color-danger) 38%, var(--border-color));

    .status-dot {
      background: var(--color-danger);
    }

    &:hover {
      border-color: color-mix(in srgb, var(--color-danger) 55%, var(--border-color));
    }
  }
}

.status-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #9CA3AF;
  &.dot-todo        { background: #9CA3AF; }
  &.dot-in_progress { background: var(--color-primary); }
  &.dot-done        { background: var(--color-success); }
  &.dot-blocked     { background: var(--color-danger); }
}

.tnc-main {
  flex: 1;
  min-width: 0;
}
.tnc-attr-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 4px;
}
.tnc-group {
  font-size: var(--fs-xs);
}
.course-chip {
  font-size: var(--fs-xs);
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-weight: 600;
  line-height: 1.3;
}
.tnc-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
  flex-wrap: wrap;
}
.tnc-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}
.tnc-desc {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* Node chips (refined) — extend global .badge pattern */
.chip {
  display: inline-flex;
  align-items: center;
  font-size: var(--fs-xs);
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  font-weight: 500;
  white-space: nowrap;
  line-height: 1.4;
}
.chip-refined { background: rgba(34, 197, 94, 0.14);      color: #15803D; }

.tnc-right {
  flex-shrink: 0;

  &--grid {
    display: grid;
    align-items: center;
    column-gap: 12px;
    /* assignees | ddl | progress | actions */
    grid-template-columns: 76px 84px 56px 72px;
  }

  &--dash {
    /* + status column before actions */
    grid-template-columns: 76px 84px 56px 96px 72px;
  }
}

.tnc-col {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  min-width: 0;

  &--assignees {
    justify-content: flex-start;
  }

  &--ddl {
    justify-content: center;
  }

  &--actions {
    justify-content: flex-end;
  }
}

.tnc-ddl-empty {
  font-size: var(--fs-sm);
  line-height: 1;
}

.assignees {
  display: inline-flex;
  align-items: center;
  .av {
    margin-left: -6px;
    border: 2px solid var(--bg-card);
    font-size: 12px;
    &:first-child { margin-left: 0; }
  }
  .av-more {
    margin-left: -4px;
    background: var(--bg-soft);
    color: var(--text-secondary);
    border: 2px solid var(--bg-card);
    width: 24px; height: 24px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
  }
  .av-empty { padding: 0 4px; }
}

.ddl-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: var(--radius-full);
  white-space: nowrap;
  .el-icon { font-size: 11px; }

  &.ddl-default { background: var(--bg-soft); color: var(--text-secondary); }
  &.ddl-warn    { background: rgba(230,162,60,0.16); color: var(--color-warning); }
  &.ddl-overdue { background: rgba(245,108,108,0.16); color: var(--color-danger); }
  &.ddl-done    { background: rgba(103,194,58,0.14); color: #15803D; }
}

.progress-wrap {
  flex-shrink: 0;
  width: 56px;
  display: flex;
  align-items: center;
}
.progress-bar {
  width: 100%;
  height: 5px;
  background: var(--bg-soft);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  transition: width 0.25s ease, background-color 0.2s ease;

  &--active {
    background: var(--color-primary);
  }

  &--done {
    background: var(--color-success);
  }

  &--blocked {
    background: var(--color-danger);
  }
}

.tnc-actions {
  display: flex;
  align-items: center;
  gap: 0;
  opacity: 0;
  transition: opacity .15s;
}

.tnc-more-btn {
  padding-inline: 6px !important;
}

.tnc-status-btn {
  min-width: 72px;
  padding-inline: 4px !important;
  font-weight: 500;

  .el-icon {
    margin-left: 2px;
    font-size: 12px;
  }

  &--todo { color: var(--text-secondary); }
  &--in_progress { color: var(--color-primary); }
  &--done { color: var(--color-success); }
  &--blocked { color: var(--color-danger); }
}

.tnc-status-readonly {
  font-size: var(--fs-sm);
  line-height: 1;
  min-width: 72px;
  text-align: center;
}

.tnc--dashboard {
  .tnc-actions {
    opacity: 1;
  }

  &:hover {
    .tnc-actions { opacity: 1; }
  }
}

@media (max-width: 900px) {
  .tnc-right--grid {
    column-gap: 8px;

    .tnc-col--progress { display: none; }
  }

  .tnc-right--grid:not(.tnc-right--dash) {
    grid-template-columns: 64px 72px 64px;
  }

  .tnc-right--dash {
    grid-template-columns: 64px 72px 96px 64px;
  }
}
</style>
