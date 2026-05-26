<template>
  <div class="aip">
    <div class="aip-head">
      <el-icon class="head-icon"><MagicStick /></el-icon>
      <span class="head-title">AI 助手</span>
      <el-button
        v-if="collapsible"
        text
        size="small"
        class="collapse-btn"
        @click="emit('collapse')"
      >
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <el-tabs v-model="mode" class="aip-tabs">
      <el-tab-pane name="gen" label="生成">
        <div class="pane gen-pane">
          <div class="hint muted tiny">
            粘贴课程要求、项目说明等，AI 将自动拆分项目树。
          </div>
          <el-input
            v-model="genInput"
            type="textarea"
            :rows="10"
            placeholder="粘贴课程要求或项目描述..."
            :disabled="genJob !== null"
          />
          <div class="gen-actions">
            <el-button size="small" @click="onUploadStub">
              <el-icon><Upload /></el-icon>&nbsp;上传文档
            </el-button>
            <span class="grow"></span>
            <el-button
              type="primary"
              :loading="genJob !== null"
              :disabled="!genInput.trim()"
              @click="onGenerate"
            >
              <el-icon><MagicStick /></el-icon>&nbsp;生成项目树
            </el-button>
          </div>

          <div v-if="genJob !== null" class="shimmer-block">
            <div class="shimmer-bar" style="width: 80%"></div>
            <div class="shimmer-bar" style="width: 60%"></div>
            <div class="shimmer-bar" style="width: 70%"></div>
            <div class="shimmer-bar" style="width: 50%"></div>
            <div class="shimmer-status muted tiny">
              AI 正在思考中… ({{ genStatus || 'running' }})
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane name="edit" label="对话编辑">
        <div class="pane edit-pane">
          <div class="msg-list" ref="msgListRef">
            <div v-if="!messages.length" class="msg-empty muted tiny">
              告诉 AI 你想如何调整项目树，例如：「把 W3 的任务拆得更细」「合并第二章和第三章」。
            </div>
            <div
              v-for="(m, i) in messages"
              :key="i"
              class="msg"
              :class="`msg-${m.role}`"
            >
              <div class="msg-bubble">
                <div class="msg-body">{{ m.text }}</div>
                <div
                  v-if="m.role === 'assistant' && m.result"
                  class="msg-actions"
                >
                  <el-button size="small" type="primary" @click="emit('apply', m.result)">
                    应用变更
                  </el-button>
                  <el-button size="small" text @click="emit('preview', m.result)">
                    预览
                  </el-button>
                </div>
              </div>
              <div v-if="m.cached" class="msg-cached tiny muted">已缓存结果</div>
            </div>
            <div v-if="editJob !== null" class="msg msg-assistant">
              <div class="msg-bubble">
                <div class="msg-thinking">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </div>
              </div>
            </div>
          </div>

          <div class="edit-input">
            <el-input
              v-model="editInput"
              type="textarea"
              :rows="2"
              placeholder="输入指令...（Ctrl + Enter 发送）"
              @keydown.ctrl.enter.prevent="onSendEdit"
              :disabled="editJob !== null"
            />
            <el-button
              type="primary"
              :loading="editJob !== null"
              :disabled="!editInput.trim()"
              @click="onSendEdit"
            >
              发送
            </el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Upload, ArrowRight } from '@element-plus/icons-vue'
import { Api } from '@/api'
import { useWS } from '@/composables/useWS'
import { useTreeStore } from '@/stores/tree'

const props = defineProps<{
  groupId: number
  collapsible?: boolean
}>()

const emit = defineEmits<{
  (e: 'collapse'): void
  (e: 'apply', result: { nodes: any[]; diff_summary?: string }): void
  (e: 'preview', result: { nodes: any[]; diff_summary?: string }): void
}>()

const treeStore = useTreeStore()
const ws = useWS()

const mode = ref<'gen' | 'edit'>('gen')

// ---- generate ----
const genInput = ref('')
const genJob = ref<number | null>(null)
const genStatus = ref<string>('')

async function onGenerate() {
  if (!genInput.value.trim()) return
  try {
    const r = await Api.aiJob('tree_gen', props.groupId, { document: genInput.value })
    genJob.value = r.id
    genStatus.value = r.status
    pollJob(r.id, 'gen')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  }
}

function onUploadStub() {
  ElMessage.info('文档上传敬请期待')
}

// ---- edit (chat) ----
const editInput = ref('')
const editJob = ref<number | null>(null)
interface Msg {
  role: 'user' | 'assistant'
  text: string
  cached?: boolean
  result?: { nodes: any[]; diff_summary?: string }
}
const messages = ref<Msg[]>([])
const msgListRef = ref<HTMLElement | null>(null)

async function onSendEdit() {
  if (!editInput.value.trim() || editJob.value !== null) return
  const text = editInput.value.trim()
  messages.value.push({ role: 'user', text })
  editInput.value = ''
  await scrollMsgs()
  try {
    const r = await Api.aiJob('tree_edit', props.groupId, {
      current_tree: { nodes: treeStore.nodes },
      instruction: text,
    })
    editJob.value = r.id
    pollJob(r.id, 'edit')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
    messages.value.push({ role: 'assistant', text: '抱歉，提交失败，请重试。' })
  }
}

async function scrollMsgs() {
  await nextTick()
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}

// ---- polling + WS ----
const pollers = new Map<number, number>()

async function checkJob(id: number, kind: 'gen' | 'edit') {
  try {
    const s = await Api.aiJobStatus(id)
    if (kind === 'gen') genStatus.value = s.status
    if (s.status === 'done' || s.status === 'succeeded' || s.status === 'completed') {
      finishJob(id, kind, s.result, false)
    } else if (s.status === 'failed' || s.status === 'error') {
      finishJobError(id, kind, s.error || 'AI 任务失败')
    }
  } catch (e: any) {
    // keep polling unless explicit 404
    if (e?.response?.status === 404) {
      finishJobError(id, kind, '任务不存在')
    }
  }
}

function pollJob(id: number, kind: 'gen' | 'edit') {
  // immediate check + 2s interval
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

function finishJob(id: number, kind: 'gen' | 'edit', result: any, fromWS: boolean) {
  clearPoll(id)
  if (kind === 'gen') {
    if (genJob.value !== id) return
    genJob.value = null
    genStatus.value = ''
    if (result && Array.isArray(result.nodes)) {
      emit('preview', result)
    } else {
      ElMessage.warning('AI 未返回有效结果')
    }
  } else {
    if (editJob.value !== id) return
    editJob.value = null
    const summary = (result && result.diff_summary) || '已生成调整方案，点击「应用变更」预览并应用。'
    const msg: Msg = {
      role: 'assistant',
      text: summary,
      cached: !!(result && result.cached),
    }
    if (result && Array.isArray(result.nodes)) msg.result = result
    messages.value.push(msg)
    void scrollMsgs()
  }
  if (!fromWS) {
    /* no-op */
  }
}

function finishJobError(id: number, kind: 'gen' | 'edit', err: string) {
  clearPoll(id)
  if (kind === 'gen' && genJob.value === id) {
    genJob.value = null
    genStatus.value = ''
    ElMessage.error(err)
  } else if (kind === 'edit' && editJob.value === id) {
    editJob.value = null
    messages.value.push({ role: 'assistant', text: `失败：${err}` })
    void scrollMsgs()
  }
}

// WS subscription
const unsubs: Array<() => void> = []
unsubs.push(
  ws.on('ai.job_progress', (data: any) => {
    const id = data?.id
    if (typeof id !== 'number') return
    const status = data?.status
    if (id === genJob.value) genStatus.value = status || ''
    if (status === 'done' || status === 'succeeded' || status === 'completed') {
      if (id === genJob.value) finishJob(id, 'gen', data.result, true)
      else if (id === editJob.value) finishJob(id, 'edit', data.result, true)
    } else if (status === 'failed' || status === 'error') {
      if (id === genJob.value) finishJobError(id, 'gen', data.error || 'AI 任务失败')
      else if (id === editJob.value) finishJobError(id, 'edit', data.error || 'AI 任务失败')
    }
  }),
)

onUnmounted(() => {
  for (const u of unsubs) {
    try { u() } catch {}
  }
  for (const id of Array.from(pollers.keys())) clearPoll(id)
})

watch(messages, () => scrollMsgs(), { deep: true })
</script>

<style lang="scss" scoped>
.aip {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  overflow: hidden;
}
.aip-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, rgba(61, 126, 255, 0.06), rgba(155, 91, 255, 0.06));

  .head-icon { font-size: 18px; color: var(--color-primary); }
  .head-title { font-weight: 600; flex: 1; }
  .collapse-btn { padding: var(--space-1); }
}

.aip-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;

  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 var(--space-4);
  }
  :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }
  :deep(.el-tab-pane) { height: 100%; }
}

.pane {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  min-height: 0;
}

.gen-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.grow { flex: 1; }

.shimmer-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--bg-soft);
  border-radius: var(--radius-md);
}

.shimmer-bar {
  height: 10px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--border-color) 0%, var(--bg-soft) 50%, var(--border-color) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Edit / chat pane */
.msg-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-right: var(--space-1);
  min-height: 200px;
}

.msg-empty { padding: var(--space-3); }

.msg {
  display: flex;
  flex-direction: column;
  &.msg-user { align-items: flex-end; }
  &.msg-assistant { align-items: flex-start; }
}

.msg-bubble {
  max-width: 90%;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--bg-soft);
  font-size: var(--fs-sm);
  line-height: 1.5;
  word-break: break-word;
}

.msg-user .msg-bubble {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.msg-actions {
  display: flex;
  gap: var(--space-1);
  margin-top: var(--space-2);
}

.msg-thinking {
  display: flex;
  gap: var(--space-1);
  padding: var(--space-1) 0;

  .dot {
    width: 6px; height: 6px;
    background: var(--color-primary);
    border-radius: 50%;
    animation: bounce 1.2s infinite;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.edit-input {
  display: flex;
  gap: var(--space-2);
  align-items: flex-end;
  border-top: 1px solid var(--border-color);
  padding-top: var(--space-3);
}
</style>
