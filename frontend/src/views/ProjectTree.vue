<template>
  <div class="pt">
    <!-- Sticky toolbar -->
    <header class="ws-toolbar pt-toolbar">
      <div class="ws-toolbar__left">
        <h1 class="ws-toolbar__title">
          <span class="t-main">项目树</span>
          <template v-if="group">
            <span class="t-sep">/</span>
            <span class="t-course">{{ group.course_name }}</span>
            <span class="t-sep">/</span>
            <span class="t-name">{{ group.name }}</span>
          </template>
        </h1>
        <span class="ws-toolbar__sep" aria-hidden="true" />
        <TreeTimelineSwitcher mode="tree" :group-id="gid" />
      </div>

      <div class="ws-toolbar__right">
        <button
          type="button"
          class="ws-chip"
          :class="{ 'is-active': focusOnMine }"
          :aria-pressed="focusOnMine"
          @click="focusOnMine = !focusOnMine"
        >
          <el-icon><Filter /></el-icon>
          仅我的
        </button>

        <template v-if="isLeader">
          <span class="ws-toolbar__sep" aria-hidden="true" />
          <el-button type="primary" round class="pt-btn-create" @click="onAddRoot">
            <el-icon><Plus /></el-icon>
            新建节点
          </el-button>
        </template>

        <span class="ws-toolbar__sep" aria-hidden="true" />

        <div class="ws-chip-group" role="group" aria-label="导入与导出">
          <button
            v-if="isLeader"
            type="button"
            class="ws-chip"
            @click="goInspiration"
          >
            <el-icon><Promotion /></el-icon>
            导入模板
          </button>
          <button type="button" class="ws-chip" @click="exportMd">
            <el-icon><Download /></el-icon>
            导出 Markdown
          </button>
        </div>
      </div>
    </header>

    <!-- Body -->
    <div
      class="pt-body"
      :class="{
        'pt-body--ai-open': showAiPanel,
        'pt-body--ai-collapsed': showAiRail,
      }"
    >
      <section class="pt-tree-col">
        <el-skeleton v-if="treeStore.loading && !treeStore.nodes.length" :rows="6" animated />
        <TreeCanvas
          v-else
          :nodes="treeStore.nodes"
          :focus-on-mine="focusOnMine"
          :current-user-id="auth.user?.id || 0"
          :selected-id="treeStore.selectedId"
          :members="members"
          @select="onSelectNode"
          @add-child="onAddChild"
          @delete="onDeleteNode"
          @drop="onDrop"
        />
      </section>

      <aside v-if="isLeader" class="pt-ai-col" :class="{ 'pt-ai-col--collapsed': aiCollapsed }">
        <div v-if="aiCollapsed" class="pt-ai-rail">
          <button
            type="button"
            class="pt-ai-rail-btn"
            title="展开 AI 助手"
            aria-label="展开 AI 助手"
            @click="aiCollapsed = false"
          >
            <el-icon><MagicStick /></el-icon>
            <span class="pt-ai-rail-label">AI</span>
          </button>
        </div>
        <div v-else class="pt-ai-panel">
          <button
            type="button"
            class="pt-ai-collapse-btn"
            title="收起 AI 助手"
            aria-label="收起 AI 助手"
            @click="aiCollapsed = true"
          >
            <el-icon><DArrowRight /></el-icon>
          </button>
          <AiChatPanel
            :group-id="gid"
            @preview="onAiPreview"
            @apply="onAiApply"
          />
        </div>
      </aside>
    </div>

    <!-- Task detail drawer -->
    <TaskDrawer
      v-model:visible="drawerOpen"
      :node="treeStore.selected"
      :members="members"
      :group="group"
      @select="onSelectNode"
      @add-child="onAddChild"
    />

    <!-- Add node dialog -->
    <el-dialog
      v-model="addDialog.open"
      :title="addDialog.parentId ? '添加子任务' : '添加根节点'"
      width="460px"
    >
      <el-form label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="addDialog.title" placeholder="任务标题" autofocus />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="addDialog.description"
            type="textarea"
            :rows="3"
            placeholder="可选"
          />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="addDialog.dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="→"
            start-placeholder="开始"
            end-placeholder="DDL"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialog.open = false">取消</el-button>
        <el-button
          type="primary"
          :loading="addDialog.busy"
          :disabled="!addDialog.title.trim()"
          @click="onConfirmAdd"
        >确认</el-button>
      </template>
    </el-dialog>

    <!-- AI diff preview modal -->
    <el-dialog
      v-model="diffDialog.open"
      title="AI 项目树预览"
      width="960px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <DiffViewer
        :old-nodes="treeStore.nodes"
        :new-nodes="diffDialog.newNodes"
        :members="members"
      />
      <div v-if="diffDialog.summary" class="diff-summary muted">
        {{ diffDialog.summary }}
      </div>
      <template #footer>
        <el-button @click="diffDialog.open = false">取消</el-button>
        <el-button
          type="primary"
          :loading="diffDialog.busy"
          @click="onConfirmApplyDiff"
        >
          确认应用
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Promotion, Download, Filter, MagicStick, DArrowRight } from '@element-plus/icons-vue'
import { Api, type MemberInfo } from '@/api'
import { useTreeStore } from '@/stores/tree'
import { useGroupsStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'
import { useWS } from '@/composables/useWS'
import TreeCanvas from '@/components/tree/TreeCanvas.vue'
import TaskDrawer from '@/components/tree/TaskDrawer.vue'
import AiChatPanel from '@/components/ai/AiChatPanel.vue'
import DiffViewer from '@/components/tree/DiffViewer.vue'
import TreeTimelineSwitcher from '@/components/common/TreeTimelineSwitcher.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()
const treeStore = useTreeStore()
const ws = useWS()

const gid = computed(() => Number(route.params.gid))
const group = computed(() => groupsStore.list.find((g) => g.id === gid.value) || null)
const isLeader = computed(() => groupsStore.currentRole === 'leader')

/** Leaders: AI expanded by default; members: no AI column (full-width tree). */
const aiCollapsed = ref(false)
const showAiPanel = computed(() => isLeader.value && !aiCollapsed.value)
const showAiRail = computed(() => isLeader.value && aiCollapsed.value)

watch(
  isLeader,
  (leader) => {
    aiCollapsed.value = !leader
  },
  { immediate: true },
)

const focusOnMine = computed({
  get: () => treeStore.focusOnMine,
  set: (v: boolean) => { treeStore.focusOnMine = v },
})

const members = ref<MemberInfo[]>([])
const drawerOpen = ref(false)
// open drawer when selectedId becomes non-zero
watch(
  () => treeStore.selectedId,
  (id) => { if (id) drawerOpen.value = true },
)

async function refreshMembers() {
  if (!gid.value) return
  try {
    members.value = await Api.members(gid.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载成员失败')
  }
}

onMounted(async () => {
  if (!gid.value) return
  groupsStore.setCurrent(gid.value)
  if (!groupsStore.loaded) {
    try { await groupsStore.refresh() } catch {}
  }
  try {
    await treeStore.load(gid.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载项目树失败')
  }
  await refreshMembers()

  // honor ?select=task_id from dashboard
  const sel = Number(route.query.select)
  if (sel) treeStore.setSelected(sel)
})

// react to route gid change (e.g. group switch)
watch(
  () => route.params.gid,
  async (g) => {
    const n = Number(g)
    if (!n || n === treeStore.groupId) return
    await treeStore.load(n)
    await refreshMembers()
  },
)

// WS subscriptions
const unsubs: Array<() => void> = []
onMounted(() => {
  unsubs.push(
    ws.on('tree.updated', (data: any) => {
      if (data?.group_id && Number(data.group_id) === gid.value) {
        treeStore.applyWSPatch(data)
      }
    }),
  )
  unsubs.push(
    ws.on('task.status_changed', (data: any) => {
      if (data?.group_id && Number(data.group_id) === gid.value) {
        // refetch tree to sync progress + statuses
        void treeStore.load(gid.value)
      }
    }),
  )
})
onUnmounted(() => {
  for (const u of unsubs) {
    try { u() } catch {}
  }
})

function onSelectNode(id: number) {
  treeStore.setSelected(id)
  drawerOpen.value = true
}

// add node flow
const addDialog = reactive({
  open: false,
  parentId: null as number | null,
  title: '',
  description: '',
  dateRange: null as [string, string] | null,
  busy: false,
})

function openAdd(parentId: number | null) {
  addDialog.open = true
  addDialog.parentId = parentId
  addDialog.title = ''
  addDialog.description = ''
  addDialog.dateRange = null
}
function onAddRoot() { openAdd(null) }
function onAddChild(parentId: number) { openAdd(parentId) }

async function onConfirmAdd() {
  if (!addDialog.title.trim()) return
  addDialog.busy = true
  try {
    await treeStore.createChild(addDialog.parentId, {
      title: addDialog.title.trim(),
      description: addDialog.description,
      start_date: addDialog.dateRange?.[0] || null,
      end_date: addDialog.dateRange?.[1] || null,
    })
    ElMessage.success('已创建')
    addDialog.open = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    addDialog.busy = false
  }
}

async function onDeleteNode(id: number) {
  const n = treeStore.byId.get(id)
  if (!n) return
  try {
    await ElMessageBox.confirm(
      `确认删除「${n.title}」及其所有子任务？`,
      '删除节点',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await treeStore.deleteNode(id)
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

async function onDrop(p: { id: number; newParentId: number | null; position: number }) {
  try {
    await treeStore.moveNode(p.id, p.newParentId, p.position)
    ElMessage.success('已移动')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '移动失败')
  }
}

const diffDialog = reactive({
  open: false,
  newNodes: [] as any[],
  summary: '',
  busy: false,
})

function onAiPreview(result: { nodes: any[]; diff_summary?: string }) {
  diffDialog.open = true
  diffDialog.newNodes = result.nodes || []
  diffDialog.summary = result.diff_summary || ''
}
function onAiApply(result: { nodes: any[]; diff_summary?: string }) {
  onAiPreview(result)
}

async function onConfirmApplyDiff() {
  if (!diffDialog.newNodes.length) {
    ElMessage.warning('没有可应用的节点')
    return
  }
  diffDialog.busy = true
  try {
    await Api.putTree(gid.value, {
      expected_version: treeStore.version,
      nodes: diffDialog.newNodes,
    })
    await treeStore.load(gid.value)
    diffDialog.open = false
    ElMessage.success('AI 方案已应用')
  } catch (e: any) {
    if (e?.response?.status === 409) {
      ElMessage.error('项目树版本已变更，请刷新后重试')
      await treeStore.load(gid.value)
    } else {
      ElMessage.error(e?.response?.data?.message || '应用失败')
    }
  } finally {
    diffDialog.busy = false
  }
}

function goInspiration() {
  router.push('/inspiration')
}

function downloadBlob(name: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function exportMd() {
  const lines: string[] = []
  if (group.value) lines.push(`# ${group.value.course_name} · ${group.value.name}`)
  else lines.push('# 项目树')
  lines.push('')
  const byParent = new Map<number | null, any[]>()
  for (const n of treeStore.nodes) {
    const pid = n.parent_id ?? null
    if (!byParent.has(pid)) byParent.set(pid, [])
    byParent.get(pid)!.push(n)
  }
  for (const arr of byParent.values()) arr.sort((a, b) => a.position - b.position)
  function walk(pid: number | null, depth: number) {
    const kids = byParent.get(pid) || []
    for (const n of kids) {
      const indent = '  '.repeat(depth)
      const check = n.status === 'done' ? 'x' : ' '
      const ddl = n.end_date ? ` _(DDL: ${n.end_date})_` : ''
      lines.push(`${indent}- [${check}] **${n.title}**${ddl}`)
      if (n.description) lines.push(`${indent}  ${n.description.split('\n')[0]}`)
      walk(n.id, depth + 1)
    }
  }
  walk(null, 0)
  const fname = `project-tree-g${treeStore.groupId}-v${treeStore.version}.md`
  downloadBlob(fname, 'text/markdown', lines.join('\n'))
}
</script>

<style lang="scss" scoped>
.pt {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ---------- Body ---------- */
.pt-body {
  /* Align AI panel top with first tree card (canvas 4px + row 2px). */
  --pt-content-inset-top: 6px;

  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
  padding: var(--space-6);
  min-height: 0;
  overflow: hidden;

  &--ai-open {
    grid-template-columns: minmax(0, 1fr) 360px;
  }

  &--ai-collapsed {
    grid-template-columns: minmax(0, 1fr) 44px;
  }
}

.pt-tree-col {
  overflow-y: auto;
  padding-right: var(--space-1);
  min-height: 0;
  min-width: 0;
}

.pt-ai-col {
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: var(--pt-content-inset-top);
  box-sizing: border-box;

  &--collapsed {
    width: 44px;
    min-width: 44px;
  }
}

.pt-ai-rail {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: var(--space-2);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.pt-ai-rail-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-2);
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 120ms ease;

  .el-icon {
    font-size: 18px;
  }

  &:hover {
    background: var(--color-primary-light);
  }
}

.pt-ai-rail-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.pt-ai-panel {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.pt-ai-collapse-btn {
  position: absolute;
  top: var(--space-2);
  left: calc(var(--space-2) * -1 - 28px);
  z-index: 2;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-tertiary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  transition:
    color 120ms ease,
    border-color 120ms ease,
    background 120ms ease;

  .el-icon {
    font-size: 14px;
  }

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
    background: var(--color-primary-light);
  }
}

/* ---------- Diff summary ---------- */
.diff-summary {
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  font-size: var(--fs-sm);
  line-height: 1.5;
}

/* ---------- Responsive ---------- */
@media (max-width: 1100px) {
  .pt-body,
  .pt-body--ai-open,
  .pt-body--ai-collapsed {
    grid-template-columns: 1fr;
    overflow: auto;
  }
  .pt-ai-col { display: none; }
}

</style>
