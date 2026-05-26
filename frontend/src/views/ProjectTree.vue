<template>
  <div class="pt">
    <!-- Sticky toolbar -->
    <header class="pt-toolbar">
      <div class="tb-left">
        <h1 class="pt-title">
          <span class="t-main">项目树</span>
          <template v-if="group">
            <span class="t-sep">/</span>
            <span class="t-course">{{ group.course_name }}</span>
            <span class="t-sep">/</span>
            <span class="t-name">{{ group.name }}</span>
          </template>
        </h1>
        <div class="view-switcher">
          <el-button-group>
            <el-button type="primary" size="small">
              <el-icon><Files /></el-icon>&nbsp;项目树
            </el-button>
            <el-button size="small" @click="router.push(`/groups/${gid}/timeline`)">
              <el-icon><Calendar /></el-icon>&nbsp;时间轴
            </el-button>
          </el-button-group>
        </div>
      </div>

      <div class="tb-right">
        <!-- Filter switch -->
        <el-switch
          v-model="focusOnMine"
          inline-prompt
          active-text="仅我的"
          inactive-text="全部"
          style="--el-switch-on-color: var(--color-primary);"
        />

        <!-- Leader: Create & AI actions -->
        <template v-if="isLeader">
          <div class="tb-divider" />
          <el-button type="primary" size="small" @click="onAddRoot">
            <el-icon><Plus /></el-icon>&nbsp;新建节点
          </el-button>
          <el-button size="small" @click="onAiGenerate">
            <el-icon><MagicStick /></el-icon>&nbsp;AI 生成
          </el-button>
          <el-button size="small" @click="onAiEdit">
            <el-icon><ChatLineRound /></el-icon>&nbsp;AI 对话
          </el-button>
          <el-button size="small" @click="goInspiration">
            <el-icon><Promotion /></el-icon>&nbsp;导入模板
          </el-button>
        </template>

        <!-- Export & info -->
        <div class="tb-divider" />
        <el-dropdown @command="onExport">
          <el-button size="small">
            <el-icon><Download /></el-icon>&nbsp;导出
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="json">JSON 格式</el-dropdown-item>
              <el-dropdown-item command="md">Markdown 格式</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-tooltip :content="`版本 ${treeStore.version} · ${members.length} 位成员`">
          <span class="info-pill">
            <el-icon><User /></el-icon>
            <span>{{ members.length }}</span>
            <span class="pill-sep">·</span>
            <span>v{{ treeStore.version }}</span>
          </span>
        </el-tooltip>

        <!-- AI panel toggle -->
        <el-tooltip v-if="aiCollapsed" content="展开 AI 助手">
          <el-button size="small" text circle @click="aiCollapsed = false">
            <el-icon><MagicStick /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </header>

    <!-- Body -->
    <div class="pt-body">
      <section class="pt-tree-col">
        <el-skeleton v-if="treeStore.loading && !treeStore.nodes.length" :rows="6" animated />
        <TreeCanvas
          v-else
          :nodes="treeStore.nodes"
          :focus-on-mine="focusOnMine"
          :current-user-id="auth.user?.id || 0"
          :current-role="groupsStore.currentRole"
          :selected-id="treeStore.selectedId"
          :members="members"
          @select="onSelectNode"
          @add-child="onAddChild"
          @delete="onDeleteNode"
          @drop="onDrop"
        />
      </section>

      <aside class="pt-ai-col" v-if="!aiCollapsed">
        <AiChatPanel
          :group-id="gid"
          :collapsible="true"
          @collapse="aiCollapsed = true"
          @preview="onAiPreview"
          @apply="onAiApply"
        />
      </aside>
    </div>

    <!-- Task detail drawer -->
    <TaskDrawer
      v-model:visible="drawerOpen"
      :node="treeStore.selected"
      :members="members"
      :current-role="groupsStore.currentRole"
      @select="onSelectNode"
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
        <el-form-item label="叶子任务">
          <el-switch v-model="addDialog.isLeaf" />
          <span class="tiny muted" style="margin-left: 8px">叶子任务可设置 DDL 与负责人</span>
        </el-form-item>
        <el-form-item v-if="addDialog.isLeaf" label="日期">
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
import {
  Plus, MagicStick, ChatLineRound, Files, ArrowDown, User,
  Calendar, Promotion, Download,
} from '@element-plus/icons-vue'
import { Api, type MemberInfo } from '@/api'
import { useTreeStore } from '@/stores/tree'
import { useGroupsStore } from '@/stores/groups'
import { useAuthStore } from '@/stores/auth'
import { useWS } from '@/composables/useWS'
import TreeCanvas from '@/components/tree/TreeCanvas.vue'
import TaskDrawer from '@/components/tree/TaskDrawer.vue'
import AiChatPanel from '@/components/ai/AiChatPanel.vue'
import DiffViewer from '@/components/tree/DiffViewer.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()
const treeStore = useTreeStore()
const ws = useWS()

const gid = computed(() => Number(route.params.gid))
const group = computed(() => groupsStore.list.find((g) => g.id === gid.value) || null)
const isLeader = computed(() => groupsStore.currentRole === 'leader')

const focusOnMine = computed({
  get: () => treeStore.focusOnMine,
  set: (v: boolean) => { treeStore.focusOnMine = v },
})

const members = ref<MemberInfo[]>([])
const drawerOpen = ref(false)
const aiCollapsed = ref(false)

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
  isLeaf: true,
  dateRange: null as [string, string] | null,
  busy: false,
})

function openAdd(parentId: number | null) {
  addDialog.open = true
  addDialog.parentId = parentId
  addDialog.title = ''
  addDialog.description = ''
  addDialog.isLeaf = parentId !== null // root is usually a composite
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
      is_leaf: addDialog.isLeaf,
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

// AI flows
function onAiGenerate() {
  aiCollapsed.value = false
  // active tab=gen handled by AiChatPanel default
}
function onAiEdit() {
  aiCollapsed.value = false
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

// export
function onExport(cmd: string) {
  if (cmd === 'json') exportJson()
  else if (cmd === 'md') exportMd()
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

function exportJson() {
  const payload = {
    group_id: treeStore.groupId,
    version: treeStore.version,
    nodes: treeStore.nodes,
  }
  const fname = `project-tree-g${treeStore.groupId}-v${treeStore.version}.json`
  downloadBlob(fname, 'application/json', JSON.stringify(payload, null, 2))
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

/* ---------- Toolbar ---------- */
.pt-toolbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  height: 56px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.tb-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  min-width: 0;
}

.tb-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.tb-divider {
  width: 1px;
  height: 18px;
  background: var(--border-subtle);
  flex-shrink: 0;
  margin: 0 var(--space-1);
}

.pt-title {
  margin: 0;
  font-size: var(--fs-base);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  overflow: hidden;

  .t-main   { color: var(--text-primary); }
  .t-sep    { color: var(--text-tertiary); font-weight: 400; font-size: var(--fs-sm); }
  .t-course { color: var(--color-primary); overflow: hidden; text-overflow: ellipsis; max-width: 120px; }
  .t-name   { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
}

.view-switcher { flex-shrink: 0; }

.info-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  padding: 3px var(--space-3);
  background: var(--bg-soft);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  white-space: nowrap;

  .pill-sep { opacity: 0.5; margin: 0 2px; }
}

/* ---------- Body ---------- */
.pt-body {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: var(--space-6);
  padding: var(--space-6);
  min-height: 0;
  overflow: hidden;
}

.pt-tree-col {
  overflow-y: auto;
  padding-right: var(--space-1);
  min-height: 0;
}

.pt-ai-col {
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  .pt-body {
    grid-template-columns: 1fr;
    overflow: auto;
  }
  .pt-ai-col { display: none; }
}

@media (max-width: 768px) {
  .pt-title .t-course,
  .pt-title .t-name { display: none; }
}
</style>
