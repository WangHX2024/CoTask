<template>
  <div class="aip">
    <header class="aip-head">
      <span class="aip-head-icon" aria-hidden="true">
        <el-icon><MagicStick /></el-icon>
      </span>
      <div class="aip-head-text">
        <span class="aip-title">CoTask AI 助手</span>
        <span class="aip-desc">
          {{ session ? '多轮对话中 · 基于上一轮草案继续调整' : '生成与对话编辑项目树' }}
        </span>
      </div>
      <button
        v-if="session || messages.length"
        type="button"
        class="insp-capsule-btn insp-capsule-btn--sm aip-new-chat"
        :disabled="pendingJob !== null"
        @click="onNewChat"
      >
        新对话
      </button>
    </header>

    <div class="aip-body">
      <div ref="msgListRef" class="aip-messages">
        <p
          v-if="!treeStore.nodes.length && !messages.length"
          class="aip-empty-hint"
        >
          输入课程要求或项目描述，AI 将生成项目树；已有任务后，可用自然语言继续调整结构。
        </p>

        <div
          v-for="(m, i) in messages"
          :key="i"
          class="aip-msg"
          :class="`aip-msg--${m.role}`"
        >
          <div class="aip-bubble">
            <p class="aip-bubble__text">{{ m.text }}</p>
            <div
              v-if="m.role === 'assistant' && m.result"
              class="aip-bubble__actions"
            >
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
                @click="emit('apply', m.result)"
              >
                应用变更
              </button>
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm"
                @click="emit('preview', m.result)"
              >
                预览
              </button>
            </div>
          </div>
          <span v-if="m.cached" class="aip-msg-meta">已缓存结果</span>
        </div>

        <div v-if="pendingJob !== null" class="aip-msg aip-msg--assistant">
          <div class="aip-bubble">
            <div v-if="pendingKind === 'gen'" class="aip-shimmer">
              <div class="aip-shimmer__bar" style="width: 80%" />
              <div class="aip-shimmer__bar" style="width: 60%" />
              <p class="aip-shimmer__status">
                AI 正在生成项目树… ({{ pendingStatus || 'running' }})
              </p>
            </div>
            <div v-else class="aip-thinking" aria-label="思考中">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>

      <footer class="aip-composer">
        <el-input
          v-model="composerInput"
          class="aip-compose-input"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
          :placeholder="composerPlaceholder"
          :disabled="pendingJob !== null"
          resize="none"
          @keydown.ctrl.enter.prevent="onSend"
          @keydown.meta.enter.prevent="onSend"
        />
        <div class="aip-composer__actions">
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm"
            :disabled="pendingJob !== null"
            @click="onUploadStub"
          >
            <el-icon><Upload /></el-icon>
            <span>上传文档</span>
          </button>
          <span class="aip-composer__grow" />
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
            :disabled="!composerInput.trim() || pendingJob !== null"
            @click="onSend"
          >
            <el-icon v-if="pendingJob === null"><MagicStick /></el-icon>
            <span>{{ pendingJob !== null ? '处理中…' : '发送' }}</span>
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Upload } from '@element-plus/icons-vue'
import { Api } from '@/api'
import { useWS } from '@/composables/useWS'
import { useTreeStore } from '@/stores/tree'
import { aiTreeContextFromFlat } from '@/utils/aiTreeContext'
import {
  clearAiSession,
  loadAiSession,
  saveAiSession,
  type AiChatScope,
  type AiSession,
} from '@/utils/aiSession'

const props = defineProps<{
  groupId: number
}>()

const emit = defineEmits<{
  (e: 'apply', result: { nodes: any[]; diff_summary?: string }): void
  (e: 'preview', result: { nodes: any[]; diff_summary?: string }): void
}>()

const treeStore = useTreeStore()
const ws = useWS()

const composerInput = ref('')
const pendingJob = ref<number | null>(null)
const pendingKind = ref<'gen' | 'edit'>('edit')
const pendingStatus = ref('')
const session = ref<AiSession | null>(null)

interface Msg {
  role: 'user' | 'assistant'
  text: string
  cached?: boolean
  result?: { nodes: any[]; diff_summary?: string; summary?: string }
}
const messages = ref<Msg[]>([])
const msgListRef = ref<HTMLElement | null>(null)

const composerPlaceholder = computed(() => {
  if (session.value) {
    return session.value.scope === 'tree_gen'
      ? '继续描述要如何调整生成的草案…'
      : '继续输入调整指令，例如：「把 PPT 任务交给张三」'
  }
  return treeStore.nodes.length
    ? '描述要如何调整项目树，例如：「把 W3 拆得更细」'
    : '粘贴课程要求或项目描述，生成完整项目树…'
})

function bindSession(id: number, scope: AiChatScope) {
  const convId = Number(id)
  if (!Number.isFinite(convId)) return
  session.value = { id: convId, scope }
  saveAiSession(props.groupId, session.value)
}

function parseAssistantPayload(content: string): { text: string; result?: Msg['result'] } {
  try {
    const d = JSON.parse(content)
    if (d && Array.isArray(d.nodes)) {
      return {
        text: d.diff_summary || d.summary || '已更新方案',
        result: {
          nodes: d.nodes,
          diff_summary: d.diff_summary,
          summary: d.summary,
        },
      }
    }
  } catch {
    /* plain text */
  }
  return { text: content.slice(0, 800) || '（无摘要）' }
}

function mapStoredMessage(m: { role: string; content: string }): Msg {
  if (m.role === 'user') {
    let text = m.content
    try {
      const d = JSON.parse(m.content)
      if (d && typeof d === 'object') {
        text = d.instruction || d.document || m.content
      }
    } catch {
      /* plain instruction */
    }
    return { role: 'user', text }
  }
  const { text, result } = parseAssistantPayload(m.content)
  const msg: Msg = { role: 'assistant', text }
  if (result) msg.result = result
  return msg
}

async function restoreSession() {
  const saved = loadAiSession(props.groupId)
  if (!saved) return
  session.value = saved
  try {
    const rows = await Api.aiMessages(saved.id)
    messages.value = rows.map(mapStoredMessage)
    const job = await Api.aiJobStatus(saved.id)
    if (job.status === 'pending' || job.status === 'streaming') {
      pendingJob.value = saved.id
      pendingKind.value = saved.scope === 'tree_gen' ? 'gen' : 'edit'
      pendingStatus.value = job.status
      pollJob(saved.id, pendingKind.value)
    }
    await scrollMsgs()
  } catch {
    resetSession(false)
  }
}

function resetSession(clearUi = true) {
  if (session.value || loadAiSession(props.groupId)) {
    clearAiSession(props.groupId)
  }
  session.value = null
  if (clearUi) {
    messages.value = []
    pendingJob.value = null
    pendingStatus.value = ''
  }
}

function onNewChat() {
  if (pendingJob.value !== null) return
  resetSession(true)
  composerInput.value = ''
}

defineExpose({ resetSession: () => resetSession(true) })

async function onSend() {
  if (!composerInput.value.trim() || pendingJob.value !== null) return
  const text = composerInput.value.trim()
  messages.value.push({ role: 'user', text })
  composerInput.value = ''
  await scrollMsgs()

  const active = session.value
  let scope: AiChatScope
  let payload: Record<string, unknown>
  let conversationId: number | undefined

  if (active) {
    scope = active.scope
    conversationId = active.id
    payload = scope === 'tree_gen' ? { instruction: text } : { instruction: text }
  } else if (!treeStore.nodes.length) {
    scope = 'tree_gen'
    payload = { document: text }
  } else {
    scope = 'tree_edit'
    payload = {
      current_tree: aiTreeContextFromFlat(treeStore.nodes),
      instruction: text,
    }
  }

  try {
    const r = await Api.aiJob(scope, props.groupId, payload, conversationId)
    if (!conversationId) bindSession(r.id, scope)
    pendingJob.value = r.id
    pendingKind.value = scope === 'tree_gen' ? 'gen' : 'edit'
    pendingStatus.value = r.status
    pollJob(r.id, pendingKind.value)
  } catch (e: any) {
    pendingJob.value = null
    ElMessage.error(e?.response?.data?.message || '提交失败')
    messages.value.push({ role: 'assistant', text: '抱歉，提交失败，请重试。' })
  }
}

function onUploadStub() {
  ElMessage.info('文档上传敬请期待')
}

async function scrollMsgs() {
  await nextTick()
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}

const pollers = new Map<number, number>()

async function checkJob(id: number, kind: 'gen' | 'edit') {
  try {
    const s = await Api.aiJobStatus(id)
    if (kind === 'gen') pendingStatus.value = s.status
    if (s.status === 'done' || s.status === 'succeeded' || s.status === 'completed') {
      finishJob(id, kind, s.result, false)
    } else if (s.status === 'failed' || s.status === 'error') {
      finishJobError(id, kind, s.error || 'AI 任务失败')
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      finishJobError(id, kind, '任务不存在')
    }
  }
}

function pollJob(id: number, kind: 'gen' | 'edit') {
  void checkJob(id, kind)
  const t = window.setInterval(() => checkJob(id, kind), 2000)
  pollers.set(id, t)
}

function clearPoll(id: number) {
  const t = pollers.get(id)
  if (t) {
    window.clearInterval(t)
    pollers.delete(id)
  }
}

function finishJob(id: number, kind: 'gen' | 'edit', result: any, _fromWS: boolean) {
  clearPoll(id)
  if (pendingJob.value !== id) return
  pendingJob.value = null
  pendingStatus.value = ''

  if (kind === 'gen') {
    if (result && Array.isArray(result.nodes)) {
      const summary =
        result?.summary || result?.diff_summary || '已生成项目树，请预览后应用。'
      messages.value.push({
        role: 'assistant',
        text: summary,
        result,
      })
      const isFirstReply = messages.value.filter((m) => m.role === 'assistant').length === 0
      if (isFirstReply) emit('preview', result)
    } else {
      ElMessage.warning('AI 未返回有效结果')
      messages.value.push({ role: 'assistant', text: '未返回有效项目树，请重试。' })
    }
  } else {
    const summary = (result && result.diff_summary) || '已生成调整方案，可预览或应用。'
    const msg: Msg = {
      role: 'assistant',
      text: summary,
      cached: !!(result && result.cached),
    }
    if (result && Array.isArray(result.nodes)) msg.result = result
    messages.value.push(msg)
  }
  void scrollMsgs()
}

function finishJobError(id: number, kind: 'gen' | 'edit', err: string) {
  clearPoll(id)
  if (pendingJob.value !== id) return
  pendingJob.value = null
  pendingStatus.value = ''
  if (kind === 'gen') {
    ElMessage.error(err)
  }
  messages.value.push({ role: 'assistant', text: `失败：${err}` })
  void scrollMsgs()
}

const unsubs: Array<() => void> = []
unsubs.push(
  ws.on('ai.job_progress', (data: any) => {
    const id = data?.job_id ?? data?.id
    if (typeof id !== 'number' || id !== pendingJob.value) return
    const status = data?.status
    pendingStatus.value = status || ''
    if (status === 'done' || status === 'succeeded' || status === 'completed') {
      finishJob(id, pendingKind.value, data.result, true)
    } else if (status === 'failed' || status === 'error') {
      finishJobError(id, pendingKind.value, data.error || 'AI 任务失败')
    }
  }),
)

onMounted(() => {
  void restoreSession()
})

onUnmounted(() => {
  for (const u of unsubs) {
    try { u() } catch {}
  }
  for (const id of Array.from(pollers.keys())) clearPoll(id)
})

watch(
  () => props.groupId,
  () => {
    resetSession(true)
    void restoreSession()
  },
)

watch(messages, () => scrollMsgs(), { deep: true })
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.aip {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.aip-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 48px;
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-primary) 9%, var(--bg-card)),
    color-mix(in srgb, #7c3aed 6%, var(--bg-card))
  );
}

.aip-head-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-primary-light);
  color: var(--color-primary);
  flex-shrink: 0;

  .el-icon {
    font-size: 16px;
  }
}

.aip-head-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.aip-new-chat {
  flex-shrink: 0;
  margin-left: auto;
}

.aip-title {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.aip-desc {
  font-size: var(--fs-xs);
  color: var(--text-tertiary);
  line-height: 1.3;
}

.aip-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.aip-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  background: var(--bg-soft);
}

.aip-empty-hint {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  line-height: 1.55;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.aip-msg {
  display: flex;
  flex-direction: column;
  max-width: 92%;

  &--user {
    align-self: flex-end;
    align-items: flex-end;
  }

  &--assistant {
    align-self: flex-start;
    align-items: flex-start;
  }
}

.aip-bubble {
  --bubble-r: 14px;
  --bubble-bg: color-mix(in srgb, var(--bg-card) 94%, var(--bg-soft));
  padding: var(--space-2) var(--space-3);
  background: var(--bubble-bg);
  border-radius: var(--bubble-r);
  box-shadow: 0 1px 0.5px color-mix(in srgb, var(--text-primary) 5%, transparent);
}

.aip-msg--user .aip-bubble {
  --bubble-bg: color-mix(in srgb, var(--color-primary) 22%, var(--bg-card));
  border-radius: var(--bubble-r) var(--bubble-r) var(--radius-xs) var(--bubble-r);
}

.aip-bubble__text {
  margin: 0;
  font-size: var(--fs-sm);
  line-height: 1.55;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.aip-msg--user .aip-bubble__text {
  color: var(--text-primary);
}

.aip-bubble__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-subtle);
}

.aip-msg-meta {
  margin-top: 4px;
  padding: 0 var(--space-1);
  font-size: var(--fs-xs);
  color: var(--text-tertiary);
}

.aip-shimmer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 180px;
}

.aip-shimmer__bar {
  height: 8px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    90deg,
    var(--border-subtle) 0%,
    var(--bg-soft) 50%,
    var(--border-subtle) 100%
  );
  background-size: 200% 100%;
  animation: aip-shimmer 1.4s linear infinite;
}

.aip-shimmer__status {
  margin: var(--space-1) 0 0;
  font-size: var(--fs-xs);
  color: var(--text-tertiary);
}

@keyframes aip-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.aip-thinking {
  display: flex;
  gap: 6px;
  padding: var(--space-1) 0;

  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-primary);
    animation: aip-bounce 1.2s infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes aip-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.aip-composer {
  flex-shrink: 0;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.aip-compose-input {
  width: 100%;

  :deep(.el-textarea__inner) {
    min-height: 72px;
    padding: var(--space-3) var(--space-4);
    font-size: var(--fs-base);
    line-height: 1.55;
    color: var(--text-primary);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: none;

    &:hover {
      border-color: var(--text-tertiary);
    }

    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary) inset;
    }
  }
}

.aip-composer__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.aip-composer__grow {
  flex: 1;
  min-width: var(--space-2);
}
</style>
