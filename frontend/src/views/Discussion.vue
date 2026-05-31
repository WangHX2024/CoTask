<template>
  <div class="disc-page">
    <!-- Mobile picker (outside split so desktop layout keeps gap) -->
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

    <div ref="discSplitRef" class="disc-split">
    <!-- LEFT channels -->
    <aside class="disc-left" :style="sidebarStyle">
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
          class="list-row ch-item"
          :class="{ 'is-active': currentChannelId === c.id }"
          @click="selectChannel(c.id)"
        >
          <span class="ch-hash">#</span>
          <span class="list-row__text">{{ c.name }}</span>
        </div>
        <div v-if="!channels.length && !loadingChannels" class="empty-tip">
          暂无频道
        </div>
      </div>
    </aside>

    <ResizeHandle
      v-model="sidebarWidth"
      class="disc-split__handle"
      :min="sidebarMin"
      :max="sidebarMax"
      storage-key="cotask.discussion.sidebar"
    />

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
          :class="{ 'msg-row--mine': isOwnMessage(m) }"
        >
          <el-avatar
            :src="m.author_avatar || undefined"
            :size="32"
            class="msg-avatar"
          >
            {{ msgInitial(m) }}
          </el-avatar>
          <div class="msg-stack">
            <div class="msg-meta">
              <span class="msg-author">{{ m.author_name || '用户' }}</span>
              <span class="msg-time" :title="m.created_at">
                {{ relativeTime(m.created_at) }}
              </span>
              <div class="msg-actions">
                <el-button text size="small" @click="onQuote(m)">
                  <el-icon><ChatDotRound /></el-icon>&nbsp;引用
                </el-button>
              </div>
            </div>
            <div class="msg-bubble" :class="{ 'msg-bubble--mine': isOwnMessage(m) }">
              <div v-if="m.quote_id" class="msg-bubble-quote">
                <span class="msg-bubble-quote-bar" aria-hidden="true" />
                <span class="msg-bubble-quote-inner">
                  <el-icon><Right /></el-icon>
                  <span>{{ quotePreview(m.quote_id) }}</span>
                </span>
              </div>
              <div class="msg-bubble-body" v-html="renderBody(m.body)"></div>
            </div>
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
        <div class="input-mid">
          <el-input
            ref="inputRef"
            v-model="draft"
            class="disc-compose-input"
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
              class="list-row mention-item"
              :class="{ 'is-active': i === mentionIdx }"
              @mousedown.prevent="pickMention(u)"
            >
              <el-avatar :src="u.avatar_url" :size="24">{{ (u.name || '?').slice(0,1) }}</el-avatar>
              <span>{{ u.name }}</span>
            </div>
          </div>
        </div>

        <div class="input-actions">
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary disc-send-btn"
            :disabled="!canSend || sending"
            @click="onSend"
          >
            <el-icon><Promotion /></el-icon>
            <span>{{ sending ? '发送中…' : '发送' }}</span>
          </button>
        </div>
      </div>
    </section>
    </div>

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
import { parseApiDate, relativeTime } from '@/utils/datetime'
import {
  Api,
  type Channel,
  type DiscussionMessage,
  type MemberInfo,
} from '@/api'
import { useGroupsStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'
import { useWS } from '@/composables/useWS'
import ResizeHandle from '@/components/common/ResizeHandle.vue'
import { useResizableWidth } from '@/composables/useResizableWidth'

const discSplitRef = ref<HTMLElement | null>(null)

const {
  width: sidebarWidth,
  style: sidebarStyle,
  minWidth: sidebarMin,
  maxWidth: sidebarMax,
  bindSplitContainer,
} = useResizableWidth({
  defaultWidth: 220,
  minWidth: 140,
  maxWidth: 520,
  mainMinWidth: 200,
})

bindSplitContainer(discSplitRef)

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
    const qChannel = Number(route.query.channel)
    if (qChannel && channels.value.some((c) => c.id === qChannel)) {
      currentChannelId.value = qChannel
    } else if (channels.value.length && !currentChannelId.value) {
      const groupCh = channels.value.find((c) => !c.task_id && c.name === '全员')
      currentChannelId.value = groupCh?.id ?? channels.value[0].id
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
      (a, b) => parseApiDate(a.created_at).valueOf() - parseApiDate(b.created_at).valueOf(),
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
function isOwnMessage(m: DiscussionMessage) {
  return !!auth.user?.id && m.author_id === auth.user.id && !m.anon
}

function msgInitial(m: DiscussionMessage) {
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
  const author = m.author_name || '?'
  const preview = body.length > 40 ? `${body.slice(0, 40)}…` : body
  return `${author}：${preview}`
}
function quotePreviewFull(m: DiscussionMessage): string {
  const author = m.author_name || '?'
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
function applyRouteChannel() {
  const qChannel = Number(route.query.channel)
  if (qChannel && channels.value.some((c) => c.id === qChannel)) {
    currentChannelId.value = qChannel
    void loadMessages()
  }
}

onMounted(async () => {
  await Promise.all([loadChannels(), loadMembers()])
  applyRouteChannel()
  if (currentChannelId.value) await loadMessages()
  setupWS()
})

watch(
  () => route.query.channel,
  () => applyRouteChannel(),
)
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

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.disc-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: var(--space-4);
  padding: var(--space-6);
  box-sizing: border-box;
}

.disc-split {
  display: flex;
  flex: 1;
  min-height: 0;
  min-width: 0;
  gap: var(--space-4);
  align-items: stretch;
}

.disc-split__handle {
  flex-shrink: 0;
  margin: 0 calc(var(--space-2) * -1);
}

/* ---------- Left channel sidebar ---------- */
.disc-left {
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.disc-left-head {
  height: 48px;
  padding: 0 var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  .disc-title {
    font-weight: 600;
    font-size: var(--fs-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

.disc-channels {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

/* Channel item — extends global .list-row with a leading "#" mark */
.ch-item .ch-hash {
  color: var(--text-tertiary);
  font-weight: 600;
  font-size: var(--fs-base);
  flex-shrink: 0;
}
.ch-item.is-active .ch-hash { color: var(--color-primary); }

/* ---------- Right message panel ---------- */
.disc-right {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.disc-header {
  height: 48px;
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  .hdr-left { display: flex; align-items: center; gap: var(--space-2); }
  .hdr-name { font-weight: 600; color: var(--text-primary); font-size: var(--fs-md); }

  .ch-hash.large {
    font-size: 18px;
    color: var(--text-tertiary);
    font-weight: 600;
  }
}

/* ---------- Message list (chat bubbles, aligned with task drawer preview) ---------- */
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  background: var(--bg-soft);
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: var(--space-2);
  max-width: min(82%, 560px);
  align-self: flex-start;

  &:hover .msg-actions {
    opacity: 1;
  }

  &--mine {
    align-self: flex-end;
    flex-direction: row-reverse;

    .msg-meta {
      flex-direction: row-reverse;
    }

    .msg-actions {
      margin-left: 0;
      margin-right: auto;
    }
  }
}

.msg-avatar {
  flex-shrink: 0;
}

.msg-stack {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.msg-row--mine .msg-stack {
  align-items: flex-end;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 4px;
  padding: 0 6px;
  font-size: var(--fs-xs);
  line-height: 1.3;
  color: var(--text-tertiary);

  .msg-author {
    color: var(--text-secondary);
    font-weight: 600;
    font-size: var(--fs-xs);
  }

  .msg-time {
    font-size: 10px;
  }

  .msg-actions {
    margin-left: auto;
    opacity: 0;
    transition: opacity 120ms ease;
  }
}

.msg-bubble {
  --bubble-r: 16px;
  --bubble-bg: color-mix(in srgb, var(--bg-card) 94%, var(--bg-soft));

  max-width: 100%;
  padding: 8px 12px 9px;
  background: var(--bubble-bg);
  border-radius: var(--bubble-r);
  box-shadow: 0 1px 0.5px color-mix(in srgb, var(--text-primary) 5%, transparent);

  &--mine {
    --bubble-bg: color-mix(in srgb, var(--color-primary) 24%, var(--bg-card));

    border-radius: var(--bubble-r) var(--bubble-r) 0 var(--bubble-r);
  }
}

.msg-bubble-quote {
  display: flex;
  align-items: stretch;
  margin-bottom: 6px;
  border-radius: 0;
  background: color-mix(in srgb, var(--text-primary) 5%, var(--bubble-bg));
}

.msg-bubble-quote-bar {
  flex-shrink: 0;
  width: 3px;
  background: var(--color-primary);
}

.msg-bubble-quote-inner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-1);
  min-width: 0;
  padding: 5px 8px;
  font-size: var(--fs-sm);
  line-height: 1.4;
  color: var(--text-secondary);
  word-break: break-word;

  .el-icon {
    flex-shrink: 0;
    margin-top: 2px;
    font-size: 12px;
  }
}

.msg-bubble-body {
  font-size: var(--fs-base);
  line-height: 1.55;
  word-break: break-word;
  white-space: pre-wrap;
  color: var(--text-primary);
}

.msg-bubble-body :deep(.at-mention) {
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: var(--radius-xs);
  padding: 0 4px;
  font-weight: 500;
}

/* ---------- Empty tip ---------- */
.empty-tip {
  padding: var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--fs-sm);

  &.big {
    padding: var(--space-10) var(--space-4);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);

    .el-icon { font-size: 36px; }
    p { margin: 0; }
  }
}

/* ---------- Quote bar ---------- */
.quote-bar {
  display: flex;
  align-items: stretch;
  border-top: 1px solid var(--border-subtle);
  background: var(--color-primary-lighter);
  font-size: var(--fs-sm);
  color: var(--text-secondary);

  &::before {
    content: '';
    flex-shrink: 0;
    width: 3px;
    background: var(--color-primary);
  }

  .el-icon,
  .quote-preview,
  .el-button {
    align-self: center;
  }

  .el-icon {
    margin-left: var(--space-3);
  }

  .quote-preview {
    flex: 1;
    min-width: 0;
    margin: 0 var(--space-2);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .el-button {
    margin-right: var(--space-2);
  }
}

/* ---------- Input bar ---------- */
.input-bar {
  /* Match send button to single-line textarea height */
  --disc-compose-h: 34px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card);
  padding: var(--space-3) var(--space-6);
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  flex-shrink: 0;

  .input-mid { flex: 1; min-width: 0; position: relative; }

  .disc-compose-input :deep(.el-textarea__inner) {
    min-height: var(--disc-compose-h);
    padding: 7px 14px;
    line-height: 20px;
    box-sizing: border-box;
    font-size: var(--fs-base);
    border-radius: var(--radius-full);
    box-shadow: 0 0 0 1px var(--border-color) inset !important;

    &:hover {
      box-shadow: 0 0 0 1px var(--text-tertiary) inset !important;
    }

    &:focus {
      box-shadow: 0 0 0 1px var(--color-primary) inset !important;
    }
  }

  .input-actions {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    align-self: flex-end;
  }

  .disc-send-btn.insp-capsule-btn {
    appearance: none;
    -webkit-appearance: none;
    height: var(--disc-compose-h);
    min-height: var(--disc-compose-h);
    min-width: 88px;
    padding: 0 var(--space-4);
    font-size: var(--fs-sm);
    flex-shrink: 0;

    .el-icon {
      font-size: 14px;
      color: inherit;
    }
  }
}

/* ---------- Mention popup ---------- */
.mention-pop {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  min-width: 200px;
  max-width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-1);
  z-index: 5;
}

/* Mention popup row — uses global .list-row */

/* ---------- Mobile channel picker ---------- */
.mobile-channel-picker {
  display: none;
  width: 100%;
  gap: var(--space-2);
  align-items: center;
  margin-bottom: var(--space-2);

  .mc-select { flex: 1; }
}

/* ---------- Responsive ---------- */
@media (max-width: 768px) {
  .disc-split {
    flex-direction: column;
    gap: 0;
  }

  .disc-left,
  .disc-split__handle { display: none; }
  .mobile-channel-picker { display: flex; }
  .disc-right { flex: 1; }
}
</style>
