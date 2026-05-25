<template>
  <div class="notify-page">
    <div class="page-head">
      <div class="head-left">
        <el-icon class="head-icon"><Bell /></el-icon>
        <h2 class="head-title">消息中心</h2>
        <el-tag v-if="notify.unread > 0" type="danger" effect="light" size="small">
          {{ notify.unread }} 条未读
        </el-tag>
      </div>
      <div class="head-right">
        <el-button :disabled="!hasUnread" :loading="marking" @click="onMarkAll">
          <el-icon><Check /></el-icon>&nbsp;全部标记为已读
        </el-button>
      </div>
    </div>

    <!-- Filter chips -->
    <div class="filter-bar">
      <div
        v-for="f in filters"
        :key="f.key"
        class="chip"
        :class="{ active: currentFilter === f.key }"
        @click="currentFilter = f.key"
      >
        {{ f.label }}
        <span v-if="f.badge != null" class="chip-badge">{{ f.badge }}</span>
      </div>
    </div>

    <el-card shadow="never" class="list-card" v-loading="loading">
      <div v-if="!filteredItems.length && !loading" class="empty-state">
        <el-icon><Bell /></el-icon>
        <p>{{ emptyText }}</p>
      </div>

      <div
        v-for="n in pagedItems"
        :key="n.id"
        class="notify-row"
        :class="{ unread: !n.read_at, urgent: isUrgent(n) }"
        @click="onRowClick(n)"
      >
        <div class="row-icon" :style="iconStyle(n.type)">
          <span class="emoji">{{ iconEmoji(n.type) }}</span>
        </div>
        <div class="row-body">
          <div class="row-title">
            <span>{{ titleOf(n) }}</span>
            <span v-if="!n.read_at" class="unread-dot" title="未读"></span>
          </div>
          <div v-if="subtitleOf(n)" class="row-sub muted tiny">
            {{ subtitleOf(n) }}
          </div>
          <div class="row-time tiny muted">
            {{ relativeTime(n.created_at) }}
          </div>
        </div>
        <div class="row-actions">
          <el-button
            v-if="taskIdOf(n)"
            text
            type="primary"
            size="small"
            @click.stop="onView(n)"
          >
            查看
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <div v-if="canLoadMore" class="load-more">
        <el-button text @click="pageSize += 20">
          加载更多
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, Check, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useNotifyStore } from '@/stores/notifications'
import type { NotificationItem } from '@/api'

const router = useRouter()
const notify = useNotifyStore()

// ---------- state ----------
const loading = ref(false)
const marking = ref(false)
const currentFilter = ref<'all' | 'unread' | 'urgent'>('all')
const pageSize = ref(30)

// ---------- derived ----------
const items = computed(() => notify.items)

const filters = computed(() => [
  { key: 'all' as const, label: '全部', badge: items.value.length || undefined },
  {
    key: 'unread' as const,
    label: '未读',
    badge: items.value.filter((n) => !n.read_at).length || undefined,
  },
  {
    key: 'urgent' as const,
    label: '紧急',
    badge: items.value.filter(isUrgent).length || undefined,
  },
])

const filteredItems = computed(() => {
  if (currentFilter.value === 'unread') {
    return items.value.filter((n) => !n.read_at)
  }
  if (currentFilter.value === 'urgent') {
    return items.value.filter(isUrgent)
  }
  return items.value
})
const pagedItems = computed(() => filteredItems.value.slice(0, pageSize.value))
const canLoadMore = computed(() => pageSize.value < filteredItems.value.length)
const hasUnread = computed(() => items.value.some((n) => !n.read_at))

const emptyText = computed(() => {
  if (currentFilter.value === 'unread') return '没有未读消息'
  if (currentFilter.value === 'urgent') return '没有紧急消息'
  return '暂无消息'
})

// ---------- load ----------
async function load() {
  loading.value = true
  try {
    await notify.refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function onMarkAll() {
  marking.value = true
  try {
    await notify.markRead()
    ElMessage.success('已全部标记为已读')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    marking.value = false
  }
}

async function onRowClick(n: NotificationItem) {
  if (n.read_at) return
  try {
    await notify.markRead([n.id])
  } catch {}
}

function onView(n: NotificationItem) {
  const tid = taskIdOf(n)
  const gid = groupIdOf(n)
  if (!tid) return
  void notify.markRead([n.id]).catch(() => {})
  if (gid) {
    router.push(`/groups/${gid}/tree?task=${tid}`)
  } else {
    router.push(`/dashboard`)
  }
}

// ---------- helpers ----------
function payloadVal(n: NotificationItem, key: string): any {
  return (n.payload || {})[key]
}
function taskIdOf(n: NotificationItem): number | null {
  const v = payloadVal(n, 'task_id')
  return typeof v === 'number' ? v : null
}
function groupIdOf(n: NotificationItem): number | null {
  const v = payloadVal(n, 'group_id')
  return typeof v === 'number' ? v : null
}
function isUrgent(n: NotificationItem): boolean {
  if (n.type === 'ddl_warning') return true
  if (payloadVal(n, 'urgent') === true) return true
  const days = payloadVal(n, 'days_left')
  if (typeof days === 'number' && days <= 1) return true
  return false
}

function titleOf(n: NotificationItem): string {
  const p = n.payload || {}
  const task = (p['task_title'] as string) || ''
  switch (n.type) {
    case 'ddl_warning': {
      const d = p['days_left']
      const dn = typeof d === 'number' ? d : 0
      if (dn <= 0) return `任务「${task}」今天截止`
      return `任务「${task}」将在 ${dn} 天后截止`
    }
    case 'nudge':
      return `你被催办：任务「${task}」`
    case 'assigned':
      return `你被分配了任务「${task}」`
    case 'mention': {
      const from = (p['from_name'] as string) || '有人'
      return `${from} 在讨论中提到了你`
    }
    default:
      return (p['title'] as string) || (p['message'] as string) || '系统消息'
  }
}
function subtitleOf(n: NotificationItem): string {
  const p = n.payload || {}
  if (n.type === 'nudge') return (p['message'] as string) || ''
  if (n.type === 'mention') return (p['snippet'] as string) || ''
  return ''
}
function iconEmoji(type: string): string {
  switch (type) {
    case 'ddl_warning': return '🔥'
    case 'nudge': return '👋'
    case 'assigned': return '📌'
    case 'mention': return '💬'
    default: return '🔔'
  }
}
function iconStyle(type: string) {
  const map: Record<string, { bg: string; fg: string }> = {
    ddl_warning: { bg: 'rgba(245,108,108,.14)', fg: 'var(--color-danger)' },
    nudge:       { bg: 'rgba(230,162,60,.14)',  fg: 'var(--color-warning)' },
    assigned:    { bg: 'rgba(61,126,255,.12)',  fg: 'var(--color-primary)' },
    mention:     { bg: 'rgba(159,122,234,.14)', fg: '#7C3AED' },
  }
  const c = map[type] || { bg: 'rgba(144,147,153,.14)', fg: 'var(--color-info)' }
  return { background: c.bg, color: c.fg }
}

function relativeTime(iso: string): string {
  const t = dayjs(iso)
  const now = dayjs()
  const diffSec = now.diff(t, 'second')
  if (diffSec < 60) return '刚刚'
  const diffMin = now.diff(t, 'minute')
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHr = now.diff(t, 'hour')
  if (diffHr < 24) return `${diffHr} 小时前`
  const diffDay = now.diff(t, 'day')
  if (diffDay === 1) return '昨天'
  if (diffDay < 7) return `${diffDay} 天前`
  return t.format('YYYY-MM-DD HH:mm')
}

// ---------- mount ----------
onMounted(() => {
  void load()
})
</script>

<style lang="scss" scoped>
.notify-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 920px;
  margin: 0 auto;
  width: 100%;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  .head-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .head-icon {
    font-size: 22px;
    color: var(--color-primary);
  }
  .head-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.filter-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
  &.active {
    background: rgba(61,126,255,.10);
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
  .chip-badge {
    background: var(--bg-soft);
    color: var(--text-secondary);
    border-radius: 999px;
    padding: 0 6px;
    font-size: 11px;
    min-width: 18px;
    text-align: center;
  }
  &.active .chip-badge {
    background: var(--color-primary);
    color: #fff;
  }
}

.list-card {
  :deep(.el-card__body) { padding: 0; }
}

.empty-state {
  padding: 60px 16px;
  text-align: center;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  .el-icon { font-size: 32px; }
  p { margin: 0; }
}

.notify-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background .15s ease;
  &:last-child { border-bottom: none; }
  &:hover { background: var(--bg-soft); }
  &.unread { background: rgba(61,126,255,.04); }
  &.unread:hover { background: rgba(61,126,255,.08); }
  &.urgent .row-title { color: var(--color-danger); }
}

.row-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  .emoji { font-size: 20px; line-height: 1; }
}

.row-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.row-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.unread-dot {
  width: 8px;
  height: 8px;
  background: var(--color-danger);
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.row-sub {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-time {
  font-size: 12px;
}
.row-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

@media (max-width: 768px) {
  .page-head { flex-direction: column; align-items: stretch; }
  .head-right { display: flex; justify-content: flex-end; }
  .row-actions {
    align-self: flex-end;
  }
}
</style>
