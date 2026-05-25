<template>
  <div
    class="tnc"
    :class="{ 'is-selected': selected, 'is-overdue': isOverdue, 'is-warning': isWarn }"
    @click="onClick"
  >
    <span class="status-dot" :class="`dot-${node.status}`" :title="statusLabel"></span>

    <div class="tnc-main">
      <div class="tnc-title-row">
        <span class="tnc-title">{{ node.title }}</span>
        <span v-if="node.is_leaf" class="chip chip-leaf" title="叶子任务">叶</span>
        <span v-if="node.refined" class="chip chip-refined" title="已细化">已细化</span>
      </div>
      <div v-if="node.description" class="tnc-desc muted">
        {{ singleLine(node.description) }}
      </div>
    </div>

    <div class="tnc-right">
      <div class="assignees">
        <template v-if="assigneeMembers.length">
          <el-tooltip
            v-for="m in assigneeMembers.slice(0, 3)"
            :key="m.user_id"
            :content="m.name"
            placement="top"
          >
            <el-avatar :size="24" :src="m.avatar_url" class="av">
              {{ (m.name || '?').slice(0, 1) }}
            </el-avatar>
          </el-tooltip>
          <span v-if="assigneeMembers.length > 3" class="av-more">+{{ assigneeMembers.length - 3 }}</span>
        </template>
        <span v-else class="av-empty tiny muted">未指派</span>
      </div>

      <div v-if="node.end_date" class="ddl-pill" :class="ddlClass">
        <el-icon><Clock /></el-icon> {{ ddlLabel }}
      </div>

      <div class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${pct}%` }"></div>
        </div>
        <span class="progress-text tiny muted">{{ pct }}%</span>
      </div>

      <div class="tnc-actions">
        <el-button size="small" text @click.stop="onClick">详情</el-button>
        <el-dropdown trigger="click" @command="onCmd" @click.stop>
          <el-button size="small" text @click.stop>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="detail">查看详情</el-dropdown-item>
              <el-dropdown-item
                v-if="canEdit"
                command="add-child"
                :disabled="node.is_leaf"
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
</template>

<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'
import { Clock, MoreFilled } from '@element-plus/icons-vue'
import type { TaskNode, MemberInfo } from '@/api'

const props = defineProps<{
  node: TaskNode
  members: MemberInfo[]
  selected?: boolean
  canEdit?: boolean
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'add-child'): void
  (e: 'delete'): void
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

const pct = computed(() => Math.max(0, Math.min(100, Math.round(props.node.progress || 0))))

const statusLabel = computed(() =>
  ({ todo: '待办', in_progress: '进行中', done: '已完成', blocked: '已阻塞' } as Record<string, string>)[
    props.node.status
  ] || props.node.status,
)

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

function onClick() {
  emit('click')
}

function onCmd(c: string) {
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
  &.is-overdue { border-left: 3px solid var(--color-danger); }
  &.is-warning { border-left: 3px solid var(--color-warning); }
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

.chip {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 600;
  white-space: nowrap;
}
.chip-leaf    { background: rgba(61,126,255,0.12); color: var(--color-primary); }
.chip-refined { background: rgba(103,194,58,0.14); color: #15803D; }

.tnc-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
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
  border-radius: 999px;
  white-space: nowrap;
  .el-icon { font-size: 11px; }

  &.ddl-default { background: var(--bg-soft); color: var(--text-secondary); }
  &.ddl-warn    { background: rgba(230,162,60,0.16); color: var(--color-warning); }
  &.ddl-overdue { background: rgba(245,108,108,0.16); color: var(--color-danger); }
  &.ddl-done    { background: rgba(103,194,58,0.14); color: #15803D; }
}

.progress-wrap {
  width: 80px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--bg-soft);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width .25s ease;
}
.progress-text { text-align: right; font-size: 10px; }

.tnc-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity .15s;
}

@media (max-width: 900px) {
  .tnc-right { gap: 8px; }
  .progress-wrap { display: none; }
}
</style>
