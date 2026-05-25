<template>
  <div class="disc-page">
    <!-- LEFT channels -->
    <aside class="disc-left">
      <div class="disc-left-head">
        <span class="disc-title">频道</span>
        <el-button text size="small" @click="openCreate" title="创建频道">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <div v-loading="loadingChannels" class="disc-channels">
        <div
          v-for="c in channels"
          :key="c.id"
          class="ch-item"
          :class="{ active: currentChannelId === c.id }"
          @click="selectChannel(c.id)"
        >
          <span class="ch-hash">#</span>
          <span class="ch-name">{{ c.name }}</span>
        </div>
        <div v-if="!channels.length && !loadingChannels" class="empty-tip">
          暂无频道
        </div>
      </div>
    </aside>

    <!-- Mobile picker -->
    <div class="mobile-channel-picker">
      <el-select
        v-model="currentChannelId"
        placeholder="选择频道"
        @change="onMobileSelect"
        class="mc-select"
      >
        <el-option
          v-for="c in channels"
          :key="c.id"
          :label="`# ${c.name}`"
          :value="c.id"
        />
      </el-select>
      <el-button size="small" @click="openCreate">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <!-- RIGHT message panel -->
    <section class="disc-right">
      <header class="disc-header">
        <div class="hdr-left">
          <span class="ch-hash large">#</span>
          <span class="hdr-name">{{ currentChannel?.name || '选择频道' }}</span>
          <el-tag v-if="currentChannel?.task_id" type="warning" size="small">任务频道</el-tag>
        </div>
        <div class="hdr-right tiny muted">
          {{ messages.length }} 条消息
        </div>
      </header>

      <div
        ref="msgListRef"
        class="msg-list"
        v-loading="loadingMessages"
      >
        <div v-if="!messages.length && !loadingMessages" class="empty-tip big">
          <el-icon><ChatLineRound /></el-icon>
          <p>还没有讨论，说点什么吧</p>
        </div>
        <div
          v-for="m in messages"
          :key="m.id"
          class="msg-row"
        >
          <el-avatar
            :src="m.anon ? '' : m.author_avatar"
            :size="36"
            class="msg-avatar"
          >
            {{ msgInitial(m) }}
          </el-avatar>
          <div class="msg-body-wrap">
            <div class="msg-meta">
              <span class="msg-author">
                {{ m.anon ? `匿名同学#${anonTag(m.author_id)}` : m.author_name }}
              </span>
              <span class="msg-time" :title="m.created_at">
                {{ relativeTime(m.created_at) }}
              </span>
              <div class="msg-actions">
                <el-button text size="small" @click="onQuote(m)">
                  <el-icon><ChatDotRound /></el-icon>&nbsp;引用
                </el-button>
              </div>
            </div>
            <div v-if="m.quote_id" class="msg-quote">
              <el-icon><Right /></el-icon>
              <span class="muted tiny">{{ quotePreview(m.quote_id) }}</span>
            </div>
            <div class="msg-body" v-html="renderBody(m.body)"></div>
          </div>
        </div>
      </div>

      <!-- Quoted preview -->
      <div v-if="quoted" class="quote-bar">
        <el-icon><ChatDotRound /></el-icon>
        <span class="quote-preview">{{ quotePreviewFull(quoted) }}</span>
        <el-button text size="small" @click="quoted = null">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <!-- Input bar -->
      <div class="input-bar">
        <div class="input-left">
          <el-switch
            v-model="anon"
            active-text="匿名"
            inline-prompt
            size="small"
          />
        </div>

        <div class="input-mid">
          <el-input
            ref="inputRef"
            v-model="draft"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="说点什么…（Ctrl/Cmd + Enter 发送，@ 提到成员）"
            @keydown="onKeydown"
            @input="onInput"
            resize="none"
          />
          <!-- @ mention dropdown -->
          <div
            v-if="mentionOpen && mentionCandidates.length"
            class="mention-pop"
          >
            <div
              v-for="(u, i) in mentionCandidates"
              :key="u.user_id"
              class="mention-item"
              :class="{ active: i === mentionIdx }"
              @mousedown.prevent="pickMention(u)"
            >
              <el-avatar :src="u.avatar_url" :size="22">{{ (u.name || '?').slice(0,1) }}</el-avatar>
              <span>{{ u.name }}</span>
            </div>
          </div>
        </div>

        <div class="input-right">
          <el-button
            type="primary"
            :disabled="!canSend"
            :loading="sending"
            @click="onSend"
          >
            <el-icon><Promotion /></el-icon>&nbsp;发送
          </el-button>
        </div>
      </div>
    </section>

    <!-- Create channel dialog -->
    <el-dialog v-model="createOpen" title="创建频道" width="420px">
      <el-form @submit.prevent>
        <el-form-item label="频道名">
          <el-input
            v-model="createName"
            placeholder="例如：产品讨论"
            maxlength="40"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, ChatLineRound, ChatDotRound, Right, Close, Promotion,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  Api,
  type Channel,
  type DiscussionMessage,
  type MemberInfo,
} from '@/api'
import { useGroupsStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'
import { useWS } from '@/composables/useWS'

const route = useRoute()
const groups = useGroupsStore()
const auth = useAuthStore()
const ws = useWS()

const gid = computed(() => Number(route.params.gid))

// ---------- state ----------
const channels = ref<(Channel & { task_id?: number })[]>([])
const currentChannelId = ref<number | null>(null)
const messages = ref<DiscussionMessage[]>([])
const members = ref<MemberInfo[]>([])
const loadingChannels = ref(false)
const loadingMessages = ref(false)

const draft = ref('')
const anon = ref(false)
const quoted = ref<DiscussionMessage | null>(null)
const sending = ref(false)

const createOpen = ref(false)
const createName = ref('')
const creating = ref(false)

const inputRef = ref<any>(null)
const msgListRef = ref<HTMLElement | null>(null)

// mention state
const mentionOpen = ref(false)
const mentionQuery = ref('')
const mentionIdx = ref(0)
const mentionStartIdx = ref(-1)

// ---------- derived ----------
const currentChannel = computed(
  () => channels.value.find((c) => c.id === currentChannelId.value) || null,
)
const canSend = computed(
  () => !!currentChannelId.value && draft.value.trim().length > 0,
)
const mentionCandidates = computed(() => {
  const q = mentionQuery.value.trim().toLowerCase()
  const list = members.value
  if (!q) return list.slice(0, 8)
  return list
    .filter((m) =>
      (m.name || '').toLowerCase().includes(q) ||
      (m.anon_id || '').toLowerCase().includes(q),
    )
    .slice(0, 8)
})

// ---------- load ----------
async function loadChannels() {
  if (!gid.value) return
  loadingChannels.value = true
  try {
    channels.value = await Api.channels(gid.value)
    if (!channels.value.length) {
      // auto-create #全员 channel
      try {
        const c = await Api.createChannel(gid.value, '全员')
        channels.value = [c]
      } catch {
        // silent: user may not have perms
      }
    }
    if (channels.value.length && !currentChannelId.value) {
      currentChannelId.value = channels.value[0].id
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载频道失败')
  } finally {
    loadingChannels.value = false
  }
}

async function loadMessages() {
  if (!gid.value || !currentChannelId.value) return
  loadingMessages.value = true
  try {
    const list = await Api.messages(gid.value, {
      channel_id: currentChannelId.value,
      limit: 80,
    })
    // server returns newest-first commonly — sort oldest first
    messages.value = [...list].sort(
      (a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf(),
    )
    await nextTick()
    scrollToBottom()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载消息失败')
  } finally {
    loadingMessages.value = false
  }
}

async function loadMembers() {
  if (!gid.value) return
  try {
    members.value = await Api.members(gid.value)
  } catch {
    members.value = []
  }
}

// ---------- selection ----------
function selectChannel(id: number) {
  if (currentChannelId.value === id) return
  currentChannelId.value = id
  void loadMessages()
}
function onMobileSelect(id: number) {
  currentChannelId.value = id
  void loadMessages()
}

// ---------- create channel ----------
function openCreate() {
  createName.value = ''
  createOpen.value = true
}
async function onCreate() {
  const name = createName.value.trim()
  if (!name) {
    ElMessage.warning('请输入频道名')
    return
  }
  creating.value = true
  try {
    const c = await Api.createChannel(gid.value, name)
    channels.value.push(c)
    currentChannelId.value = c.id
    createOpen.value = false
    ElMessage.success('频道已创建')
    void loadMessages()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

// ---------- send ----------
async function onSend() {
  if (!canSend.value || sending.value) return
  const body = draft.value.trim()
  if (!body) return
  sending.value = true
  try {
    const payload: any = {
      channel_id: currentChannelId.value,
      body,
      anon: anon.value,
    }
    if (quoted.value) payload.quote_id = quoted.value.id
    const msg = await Api.postMessage(gid.value, payload)
    messages.value.push(msg)
    draft.value = ''
    quoted.value = null
    mentionOpen.value = false
    await nextTick()
    scrollToBottom()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function onQuote(m: DiscussionMessage) {
  quoted.value = m
  nextTick(() => {
    const el = inputRef.value?.$el?.querySelector('textarea')
    el?.focus()
  })
}

// ---------- keyboard ----------
function onKeydown(ev: KeyboardEvent) {
  // mention navigation
  if (mentionOpen.value && mentionCandidates.value.length) {
    if (ev.key === 'ArrowDown') {
      mentionIdx.value = (mentionIdx.value + 1) % mentionCandidates.value.length
      ev.preventDefault()
      return
    }
    if (ev.key === 'ArrowUp') {
      mentionIdx.value =
        (mentionIdx.value - 1 + mentionCandidates.value.length) %
        mentionCandidates.value.length
      ev.preventDefault()
      return
    }
    if (ev.key === 'Enter' && !ev.ctrlKey && !ev.metaKey && !ev.shiftKey) {
      pickMention(mentionCandidates.value[mentionIdx.value])
      ev.preventDefault()
      return
    }
    if (ev.key === 'Escape') {
      mentionOpen.value = false
      ev.preventDefault()
      return
    }
  }

  // Cmd / Ctrl + Enter to send
  if ((ev.metaKey || ev.ctrlKey) && ev.key === 'Enter') {
    ev.preventDefault()
    void onSend()
  }
}

function onInput() {
  const ta = inputRef.value?.$el?.querySelector('textarea') as HTMLTextAreaElement
  if (!ta) return
  const pos = ta.selectionStart || 0
  const text = draft.value
  // find last @ before cursor (no whitespace between)
  let idx = -1
  for (let i = pos - 1; i >= 0; i--) {
    const ch = text[i]
    if (ch === '@') { idx = i; break }
    if (/\s/.test(ch)) break
  }
  if (idx === -1) {
    mentionOpen.value = false
    mentionStartIdx.value = -1
    return
  }
  const query = text.slice(idx + 1, pos)
  if (/\s/.test(query)) {
    mentionOpen.value = false
    return
  }
  mentionStartIdx.value = idx
  mentionQuery.value = query
  mentionIdx.value = 0
  mentionOpen.value = true
}

function pickMention(u: MemberInfo) {
  const ta = inputRef.value?.$el?.querySelector('textarea') as HTMLTextAreaElement
  const text = draft.value
  const pos = ta?.selectionStart || text.length
  if (mentionStartIdx.value < 0) {
    mentionOpen.value = false
    return
  }
  const before = text.slice(0, mentionStartIdx.value)
  const after = text.slice(pos)
  const insertion = `@${u.name} `
  draft.value = before + insertion + after
  mentionOpen.value = false
  mentionStartIdx.value = -1
  nextTick(() => {
    const newPos = before.length + insertion.length
    ta?.setSelectionRange(newPos, newPos)
    ta?.focus()
  })
}

// ---------- helpers ----------
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
function anonTag(uid: number) {
  return (uid * 7919) % 10000
}
function msgInitial(m: DiscussionMessage) {
  if (m.anon) return '匿'
  return (m.author_name || '?').slice(0, 1)
}
function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
function renderBody(body: string): string {
  const safe = escapeHtml(body)
  // highlight @mentions: @name<space or end>
  return safe.replace(
    /@([一-龥A-Za-z0-9_]+)/g,
    '<span class="at-mention">@$1</span>',
  )
}
function quotePreview(qid: number): string {
  const m = messages.value.find((x) => x.id === qid)
  if (!m) return '引用的消息'
  const body = (m.body || '').replace(/\s+/g, ' ')
  const author = m.anon ? '匿名同学' : (m.author_name || '?')
  const preview = body.length > 40 ? `${body.slice(0, 40)}…` : body
  return `${author}：${preview}`
}
function quotePreviewFull(m: DiscussionMessage): string {
  const author = m.anon ? '匿名同学' : (m.author_name || '?')
  const body = (m.body || '').replace(/\s+/g, ' ')
  const preview = body.length > 60 ? `${body.slice(0, 60)}…` : body
  return `回复 ${author}：${preview}`
}
function scrollToBottom() {
  const el = msgListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// ---------- WS ----------
let off: (() => void) | null = null

function setupWS() {
  off = ws.on('discussion.message', (raw: unknown) => {
    const m = raw as DiscussionMessage & { channel_id?: number }
    if (!m) return
    if (m.channel_id !== currentChannelId.value) return
    if (messages.value.some((x) => x.id === m.id)) return
    // avoid double-echo of just-sent author
    if (m.author_id === auth.user?.id) return
    messages.value.push(m)
    nextTick(() => scrollToBottom())
  })
}

// ---------- mount ----------
onMounted(async () => {
  await Promise.all([loadChannels(), loadMembers()])
  if (currentChannelId.value) await loadMessages()
  setupWS()
})
onUnmounted(() => {
  if (off) off()
})

watch(gid, async () => {
  currentChannelId.value = null
  messages.value = []
  await Promise.all([loadChannels(), loadMembers()])
  if (currentChannelId.value) await loadMessages()
})
</script>

<style lang="scss" scoped>
.disc-page {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.disc-left {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.disc-left-head {
  height: 44px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  .disc-title { font-weight: 600; font-size: 13px; color: var(--text-primary); }
}
.disc-channels {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}
.ch-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
  &:hover { background: var(--bg-soft); }
  &.active {
    background: rgba(61,126,255,.10);
    color: var(--color-primary);
  }
  .ch-hash { color: var(--text-tertiary); font-weight: 600; }
  .ch-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.disc-right {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.disc-header {
  height: 50px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  .hdr-left { display: flex; align-items: center; gap: 8px; }
  .hdr-name { font-weight: 600; color: var(--text-primary); font-size: 15px; }
  .ch-hash.large {
    font-size: 18px;
    color: var(--text-tertiary);
    font-weight: 600;
  }
}

.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.msg-row {
  display: flex;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  &:hover {
    background: var(--bg-soft);
    .msg-actions { opacity: 1; }
  }
}
.msg-avatar { flex-shrink: 0; }
.msg-body-wrap { flex: 1; min-width: 0; }
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  .msg-author { color: var(--text-primary); font-weight: 600; font-size: 13px; }
  .msg-actions {
    margin-left: auto;
    opacity: 0;
    transition: opacity .15s ease;
  }
}
.msg-quote {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-left: 3px solid var(--border-color);
  background: var(--bg-soft);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin: 4px 0;
  font-size: 12px;
}
.msg-body {
  font-size: 14px;
  line-height: 1.55;
  word-break: break-word;
  white-space: pre-wrap;
  color: var(--text-primary);
}
.msg-body :deep(.at-mention) {
  color: var(--color-primary);
  background: rgba(61,126,255,.10);
  border-radius: 4px;
  padding: 0 4px;
  font-weight: 500;
}

.empty-tip {
  padding: 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
  &.big {
    padding: 60px 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    .el-icon { font-size: 36px; }
    p { margin: 0; }
  }
}

.quote-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--bg-soft);
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-secondary);
  .quote-preview {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.input-bar {
  border-top: 1px solid var(--border-color);
  background: var(--bg-card);
  padding: 10px 14px;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  .input-left { padding-bottom: 4px; }
  .input-mid {
    flex: 1;
    min-width: 0;
    position: relative;
  }
  .input-right {
    padding-bottom: 0;
  }
}

.mention-pop {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  min-width: 200px;
  max-width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 4px;
  z-index: 5;
}
.mention-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  &:hover, &.active {
    background: rgba(61,126,255,.10);
    color: var(--color-primary);
  }
}

.mobile-channel-picker {
  display: none;
  width: 100%;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  .mc-select { flex: 1; }
}

@media (max-width: 768px) {
  .disc-page { flex-direction: column; }
  .disc-left { display: none; }
  .mobile-channel-picker { display: flex; }
  .disc-right { flex: 1; }
}
</style>
