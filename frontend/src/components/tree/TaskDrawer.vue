<template>
  <el-drawer
    class="task-drawer-el"
    :model-value="visible"
    :with-header="false"
    direction="rtl"
    size="480px"
    :destroy-on-close="false"
    :before-close="handleClose"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
  >
    <div v-if="node" class="task-drawer">
      <header class="task-drawer__head">
        <nav v-if="taskBreadcrumb.length > 1" class="task-drawer__crumb" aria-label="任务路径">
          <template v-for="(seg, i) in taskBreadcrumb" :key="i">
            <span v-if="i > 0" class="crumb-sep">/</span>
            <span :class="{ 'crumb-current': i === taskBreadcrumb.length - 1 }">{{ seg }}</span>
          </template>
        </nav>
        <div class="task-drawer__head-main">
          <div class="task-drawer__title-row">
            <span
              class="task-drawer__status-dot"
              :class="`dot-${dirty.status}`"
              :title="statusLabel"
            />
            <div class="task-drawer__title-wrap">
              <el-input
                v-if="titleEditing && canEdit"
                ref="titleInputRef"
                v-model="dirty.title"
                placeholder="任务标题"
                class="task-drawer__title-input insp-capsule-input"
                @blur="finishTitleEdit"
                @keyup.enter="finishTitleEdit"
              />
              <h2 v-else class="task-drawer__title-display">
                {{ dirty.title || '未命名任务' }}
              </h2>
            </div>
            <button
              v-if="canEdit && !titleEditing"
              type="button"
              class="task-drawer__title-edit-btn"
              title="编辑标题"
              @click="startTitleEdit"
            >
              <el-icon><EditPen /></el-icon>
            </button>
          </div>

          <div class="task-drawer__meta">
            <el-select
              v-if="!hasChildren"
              v-model="dirty.status"
              class="task-drawer__meta-status insp-capsule-select"
              :disabled="!canChangeStatus"
            >
              <el-option value="todo" label="待办" />
              <el-option value="in_progress" label="进行中" />
              <el-option value="done" label="已完成" />
              <el-option value="blocked" label="已阻塞" />
            </el-select>
            <span
              v-else
              class="task-drawer__status-readonly"
              title="存在子任务，状态由子任务汇总"
            >
              <span
                class="task-drawer__status-dot dot-inline"
                :class="`dot-${dirty.status}`"
                aria-hidden="true"
              />
              <span class="task-drawer__status-text">{{ statusLabel }}</span>
            </span>
            <el-date-picker
              v-model="dateRange"
              class="task-drawer__date insp-capsule-input"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="→"
              start-placeholder="开始"
              end-placeholder="DDL"
              clearable
              :disabled="!canEdit"
            />
          </div>
        </div>
      </header>

      <div class="task-drawer__body">
        <!-- Assignees -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">负责人</span>
            <div v-if="canEdit" class="task-drawer__block-actions">
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm"
                @click="showAiSuggest = true"
              >
                <el-icon><MagicStick /></el-icon>
                <span>AI 建议</span>
              </button>
            </div>
          </div>
          <p v-if="canEdit" class="task-drawer__block-sub">
            负责人可编辑本节点及全部下级任务
          </p>
          <div class="task-drawer__assign-row">
            <el-tooltip
              v-for="uid in dirty.assignees"
              :key="uid"
              :content="memberMap.get(uid)?.name || '未知用户'"
              placement="top"
            >
              <span class="task-drawer__assign-chip">
                <el-avatar :size="24" :src="memberMap.get(uid)?.avatar_url">
                  {{ (memberMap.get(uid)?.name || '?').slice(0, 1) }}
                </el-avatar>
                <span>{{ memberMap.get(uid)?.name || '?' }}</span>
                <el-icon
                  v-if="canEdit"
                  class="chip-x"
                  @click.stop="removeAssignee(uid)"
                ><Close /></el-icon>
              </span>
            </el-tooltip>
            <el-popover
              v-if="canEdit"
              v-model:visible="assigneePickerOpen"
              trigger="click"
              placement="bottom-start"
              :width="300"
              popper-class="task-drawer-assign-popper"
            >
              <template #reference>
                <button
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--icon insp-capsule-btn--sm"
                  title="添加负责人"
                >
                  <el-icon><Plus /></el-icon>
                </button>
              </template>
              <div class="assign-picker">
                <el-input
                  v-model="assigneeFilter"
                  class="assign-picker__search insp-capsule-input"
                  placeholder="搜索成员"
                  clearable
                />
                <ul v-if="filteredMembersForPicker.length" class="assign-picker__list">
                  <li
                    v-for="m in filteredMembersForPicker"
                    :key="m.user_id"
                    class="list-row list-row--lg"
                    :class="{ 'is-active': dirty.assignees.includes(m.user_id) }"
                    @click="toggleAssignee(m.user_id)"
                  >
                    <el-avatar :size="28" :src="m.avatar_url">
                      {{ (m.name || '?').slice(0, 1) }}
                    </el-avatar>
                    <span class="list-row__text">{{ m.name }}</span>
                    <el-icon
                      v-if="dirty.assignees.includes(m.user_id)"
                      class="assign-picker__check"
                    ><Select /></el-icon>
                  </li>
                </ul>
                <p v-else class="assign-picker__empty">无匹配成员</p>
              </div>
            </el-popover>
            <span
              v-if="!dirty.assignees.length && !canEdit"
              class="task-drawer__assign-empty"
            >未指派</span>
            <span
              v-else-if="!dirty.assignees.length && canEdit"
              class="task-drawer__assign-empty"
            >点击 + 选择</span>
          </div>
        </section>

        <!-- Description -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">描述</span>
          </div>
          <el-input
            v-model="dirty.description"
            class="insp-capsule-textarea"
            type="textarea"
            :rows="4"
            placeholder="补充任务描述、目标、产出标准…"
            :disabled="!canEdit"
          />
        </section>

        <!-- Dependencies -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">前置依赖</span>
          </div>
          <el-select
            v-model="dirty.dependencies"
            class="insp-capsule-select"
            multiple
            filterable
            placeholder="选择前置任务"
            :disabled="!canEdit"
          >
            <el-option
              v-for="n in dependableNodes"
              :key="n.id"
              :value="n.id"
              :label="n.title"
            />
          </el-select>
        </section>

        <!-- Children -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">子任务 · {{ children.length }}</span>
            <div v-if="canEdit" class="task-drawer__block-actions">
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
                @click="onAddChild"
              >
                <el-icon><Plus /></el-icon>
                <span>添加子任务</span>
              </button>
            </div>
          </div>
          <ul v-if="children.length" class="task-drawer__list">
            <li
              v-for="c in children"
              :key="c.id"
              class="list-row list-row--lg"
              @click="emit('select', c.id)"
            >
              <span
                class="task-drawer__status-dot dot-inline"
                :class="`dot-${c.status}`"
              />
              <span class="list-row__text">{{ c.title }}</span>
              <span
                class="task-drawer__child-bar"
                :style="childProgressStyle(c)"
                :title="childProgressTitle(c)"
              />
            </li>
          </ul>
          <div v-else class="task-drawer__empty">
            <p>暂无子任务</p>
          </div>
          <p v-if="canEdit && children.length" class="task-drawer__hint">
            各子任务的负责人请在该子任务详情中设置。
          </p>
        </section>

        <!-- Files -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">附件 · {{ taskFiles.length }}</span>
            <div class="task-drawer__block-actions">
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm"
                @click="goFiles"
              >
                <el-icon><Document /></el-icon>
                <span>文件库</span>
              </button>
            </div>
          </div>
          <el-skeleton v-if="loadingFiles" :rows="2" animated />
          <ul v-else-if="taskFiles.length" class="task-drawer__list">
            <li
              v-for="f in taskFiles"
              :key="f.id"
              class="list-row"
            >
              <el-icon class="list-row__icon"><Document /></el-icon>
              <span class="list-row__text" :title="f.filename">{{ f.filename }}</span>
              <span class="list-row__suffix">{{ formatSize(f.size) }}</span>
              <a
                class="badge badge--primary badge--pill"
                :href="f.download_url"
                target="_blank"
                rel="noopener"
                @click.stop
              >下载</a>
            </li>
          </ul>
          <div v-else class="task-drawer__empty">
            <p>暂无归属本任务的文件</p>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--sm"
              @click="goFiles"
            >
              前往文件库上传
            </button>
          </div>
        </section>

        <!-- Related inspirations -->
        <section class="task-drawer__block">
          <div class="task-drawer__block-head">
            <span class="task-drawer__block-title">相关灵感</span>
            <div class="task-drawer__block-actions">
              <button
                type="button"
                class="insp-capsule-btn insp-capsule-btn--sm"
                @click="goInspirationSearch"
              >
                灵感广场
              </button>
            </div>
          </div>
          <p v-if="relatedKeywords.length" class="task-drawer__block-sub">
            按「{{ relatedKeywords.join('」「') }}」检索并合并
          </p>
          <el-skeleton v-if="loadingPosts" :rows="3" animated />
          <ul v-else-if="relatedPosts.length" class="task-drawer__insp-list">
            <li
              v-for="p in relatedPosts"
              :key="p.id"
              class="task-drawer__insp-item"
              @click="goPost(p.id)"
            >
              <span class="insp-tag" :class="`cat-${p.category}`">
                {{ categoryLabel(p.category) }}
              </span>
              <div class="insp-item-main">
                <div class="insp-item-title">{{ p.title }}</div>
                <div class="insp-item-meta">
                  <span v-if="p.matched_keyword" class="insp-match">
                    匹配「{{ p.matched_keyword }}」
                  </span>
                  <span v-if="p.matched_keyword"> · </span>
                  {{ p.anon ? '匿名' : p.author_name }}
                  <span v-if="p.likes"> · {{ p.likes }} 赞</span>
                </div>
              </div>
            </li>
          </ul>
          <div v-else class="task-drawer__empty">
            <p>未找到与当前任务路径相关的灵感</p>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--sm"
              @click="goInspirationSearch"
            >
              去灵感广场搜索
            </button>
          </div>
        </section>

        <!-- Discussion -->
        <section class="task-drawer__block task-drawer__block--compact">
          <div class="task-drawer__block-head task-drawer__block-head--only">
            <span class="task-drawer__block-title">讨论</span>
          </div>
          <div class="task-drawer__disc-card">
            <div class="task-drawer__disc-glass task-drawer__disc-glass--light" aria-hidden="true" />
            <div class="task-drawer__disc-glass task-drawer__disc-glass--heavy" aria-hidden="true" />
            <div class="task-drawer__disc-card-inner">
              <p
                class="task-drawer__disc-card-title"
                :class="{ 'is-placeholder': !taskChannel }"
              >
                {{ taskChannel?.name ?? '尚未创建任务讨论频道' }}
              </p>
              <div class="task-drawer__disc-card-scroll">
                <ul
                  v-if="taskChannel && taskPreviewMessages.length"
                  class="task-drawer__disc-preview-msgs"
                >
                  <li
                    v-for="m in taskPreviewMessages"
                    :key="m.id"
                    class="disc-bubble-row"
                    :class="{ 'disc-bubble-row--mine': isOwnPreviewMessage(m) }"
                  >
                    <span class="disc-bubble-meta">{{ m.author_name }}</span>
                    <div
                      class="disc-bubble"
                      :class="{ 'disc-bubble--mine': isOwnPreviewMessage(m) }"
                    >
                      <span class="disc-bubble__text">{{ previewMessageBody(m.body) }}</span>
                    </div>
                  </li>
                </ul>
                <p v-else-if="taskChannel" class="task-drawer__disc-card-empty">暂无消息</p>
              </div>
              <div class="task-drawer__disc-card-action">
                <button
                  v-if="!taskChannel"
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
                  :disabled="creatingTaskChannel"
                  @click="createTaskChannel"
                >
                  <span>{{ creatingTaskChannel ? '创建中…' : '创建任务频道' }}</span>
                </button>
                <button
                  v-else
                  type="button"
                  class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
                  @click="enterTaskDiscussion"
                >
                  <span>进入任务讨论</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <footer class="task-drawer__foot">
        <div class="task-drawer__foot-left">
          <button
            v-if="canNudge"
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm"
            :disabled="nudging"
            @click="onNudge"
          >
            <el-icon><Bell /></el-icon>
            <span>{{ nudging ? '发送中…' : '催办' }}</span>
          </button>
          <button
            v-if="canEdit"
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--danger"
            @click="onDelete"
          >
            <el-icon><Delete /></el-icon>
            <span>删除</span>
          </button>
        </div>
        <div class="task-drawer__foot-right">
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm"
            @click="emit('update:visible', false)"
          >
            关闭
          </button>
          <button
            v-if="canSave"
            type="button"
            class="insp-capsule-btn insp-capsule-btn--sm insp-capsule-btn--primary"
            :disabled="!isDirty || saving"
            @click="onSave"
          >
            <span>{{ saving ? '保存中…' : '保存' }}</span>
          </button>
        </div>
      </footer>
    </div>

    <!-- AI suggestion dialog -->
    <el-dialog
      v-model="showAiSuggest"
      title="AI 建议负责人"
      width="420px"
      append-to-body
    >
      <p class="muted">基于成员技能与任务标题的匹配，建议从以下成员中分配：</p>
      <ul class="ai-suggest-list">
        <li v-for="s in aiSuggestions" :key="s.user_id">
          <el-avatar :size="28" :src="s.avatar_url">{{ s.name.slice(0,1) }}</el-avatar>
          <span class="s-name">{{ s.name }}</span>
          <span class="s-reason tiny muted">{{ s.reason }}</span>
          <el-button size="small" type="primary" plain @click="applySuggestion(s.user_id)">
            采纳
          </el-button>
        </li>
      </ul>
      <template #footer>
        <el-button @click="showAiSuggest = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Close, Plus, Delete, Bell, MagicStick, Document, Select, EditPen,
} from '@element-plus/icons-vue'
import {
  Api,
  type Channel,
  type DiscussionMessage,
  type FileInfo,
  type GroupBrief,
  type TaskNode,
  type MemberInfo,
  type PostBrief,
} from '@/api'
import { useTreeStore } from '@/stores/tree'
import { useAuthStore } from '@/stores/auth'
import { taskBarPercent } from '@/utils/taskProgress'

const props = defineProps<{
  visible: boolean
  node: TaskNode | null
  members: MemberInfo[]
  group?: GroupBrief | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'select', id: number): void
  (e: 'add-child', parentId: number): void
}>()

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const treeStore = useTreeStore()

const canEdit = computed(() => !!props.node?.can_manage)
const isAssignee = computed(
  () => !!props.node && (props.node.assignees || []).includes(auth.user?.id || 0),
)
const hasChildren = computed(() => !!props.node && !props.node.is_leaf)
const canChangeStatus = computed(
  () => (canEdit.value || isAssignee.value) && !hasChildren.value,
)
const canSave = computed(() => canEdit.value || isAssignee.value)
const nudgeTargetIds = computed(() => {
  const me = auth.user?.id || 0
  return (props.node?.assignees || []).filter((uid) => uid !== me)
})
const canNudge = computed(
  () => (canEdit.value || isAssignee.value) && nudgeTargetIds.value.length > 0,
)

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    todo: '待办',
    in_progress: '进行中',
    done: '已完成',
    blocked: '已阻塞',
  }
  return map[dirty.status] || dirty.status
})

const dirty = reactive({
  title: '',
  description: '',
  status: 'todo' as TaskNode['status'],
  assignees: [] as number[],
  dependencies: [] as number[],
  start_date: '' as string,
  end_date: '' as string,
})

const dateRange = computed<[string, string] | null>({
  get() {
    if (dirty.start_date || dirty.end_date) {
      return [dirty.start_date || '', dirty.end_date || '']
    }
    return null
  },
  set(v) {
    dirty.start_date = v?.[0] || ''
    dirty.end_date = v?.[1] || ''
  },
})

const titleEditing = ref(false)
const titleInputRef = ref<{ focus?: () => void; input?: HTMLInputElement } | null>(null)

async function startTitleEdit() {
  if (!canEdit.value) return
  titleEditing.value = true
  await nextTick()
  titleInputRef.value?.focus?.()
  const el =
    titleInputRef.value?.input ||
    (titleInputRef.value as { $el?: HTMLElement })?.$el?.querySelector?.('input')
  ;(el as HTMLInputElement | undefined)?.focus?.()
}

function finishTitleEdit() {
  titleEditing.value = false
}

/** Latest node from store — never use stale props.node for version / assignees. */
const liveNode = computed(() => {
  const id = props.node?.id
  if (!id) return null
  return treeStore.byId.get(id) ?? null
})

function resyncDirtyFromStore() {
  const n = liveNode.value
  if (n) syncDirtyFromNode(n)
}

type DirtySnapshot = {
  title: string
  description: string
  status: TaskNode['status']
  assignees: number[]
  dependencies: number[]
  start_date: string
  end_date: string
}

function syncDirtyFromNode(node: TaskNode) {
  titleEditing.value = false
  dirty.title = node.title
  dirty.description = node.description || ''
  dirty.status = node.status
  dirty.assignees = [...(node.assignees || [])]
  dirty.dependencies = [...(node.dependencies || [])]
  dirty.start_date = node.start_date || ''
  dirty.end_date = node.end_date || ''
}

function captureDirtySnapshot(): DirtySnapshot {
  return {
    title: dirty.title,
    description: dirty.description,
    status: dirty.status,
    assignees: [...dirty.assignees],
    dependencies: [...dirty.dependencies],
    start_date: dirty.start_date,
    end_date: dirty.end_date,
  }
}

function applyDirtySnapshot(snapshot: DirtySnapshot) {
  dirty.title = snapshot.title
  dirty.description = snapshot.description
  dirty.status = snapshot.status
  dirty.assignees = [...snapshot.assignees]
  dirty.dependencies = [...snapshot.dependencies]
  dirty.start_date = snapshot.start_date
  dirty.end_date = snapshot.end_date
}

watch(
  () => (props.visible && props.node?.id ? props.node.id : 0),
  (id) => {
    if (!id || !props.visible) return
    resyncDirtyFromStore()
  },
  { immediate: true },
)

watch(
  () => props.visible,
  (open) => {
    if (open) resyncDirtyFromStore()
  },
)

const memberMap = computed(() => {
  const m = new Map<number, MemberInfo>()
  for (const x of props.members) m.set(x.user_id, x)
  return m
})

const children = computed(() => {
  if (!props.node) return []
  return treeStore.childrenOf(props.node.id)
})

const taskBreadcrumb = computed(() => {
  if (!props.node?.path) {
    return props.node?.title ? [props.node.title] : []
  }
  const titles: string[] = []
  for (const seg of props.node.path.split('/')) {
    if (!seg || !/^\d+$/.test(seg)) continue
    const n = treeStore.byId.get(Number(seg))
    if (n?.title) titles.push(n.title)
  }
  return titles
})

const dependableNodes = computed<TaskNode[]>(() =>
  treeStore.nodes.filter((n) => props.node && n.id !== props.node.id),
)

const isDirty = computed(() => {
  const base = liveNode.value
  if (!base) return false
  return (
    dirty.title !== base.title ||
    dirty.description !== (base.description || '') ||
    dirty.status !== base.status ||
    !sameArr(dirty.assignees, base.assignees || []) ||
    !sameArr(dirty.dependencies, base.dependencies || []) ||
    dirty.start_date !== (base.start_date || '') ||
    dirty.end_date !== (base.end_date || '')
  )
})
function sameArr(a: number[], b: number[]) {
  if (a.length !== b.length) return false
  const sa = [...a].sort()
  const sb = [...b].sort()
  return sa.every((x, i) => x === sb[i])
}

function removeAssignee(uid: number) {
  dirty.assignees = dirty.assignees.filter((x) => x !== uid)
}

const assigneePickerOpen = ref(false)
const assigneeFilter = ref('')

const filteredMembersForPicker = computed(() => {
  const q = assigneeFilter.value.trim().toLowerCase()
  if (!q) return props.members
  return props.members.filter((m) => (m.name || '').toLowerCase().includes(q))
})

function toggleAssignee(uid: number) {
  const idx = dirty.assignees.indexOf(uid)
  if (idx >= 0) dirty.assignees.splice(idx, 1)
  else dirty.assignees.push(uid)
}

watch(assigneePickerOpen, (open) => {
  if (!open) assigneeFilter.value = ''
})

function buildPatch(base: TaskNode, snapshot: DirtySnapshot) {
  const patch: Record<string, unknown> = { expected_version: base.version }
  if (canEdit.value) {
    if (snapshot.title !== base.title) patch.title = snapshot.title
    if (snapshot.description !== (base.description || '')) patch.description = snapshot.description
    if (!sameArr(snapshot.assignees, base.assignees || [])) patch.assignees = snapshot.assignees
    if (!sameArr(snapshot.dependencies, base.dependencies || [])) {
      patch.dependencies = snapshot.dependencies
    }
    if (snapshot.start_date !== (base.start_date || '')) {
      patch.start_date = snapshot.start_date || null
    }
    if (snapshot.end_date !== (base.end_date || '')) {
      patch.end_date = snapshot.end_date || null
    }
  }
  if (base.is_leaf && snapshot.status !== base.status) patch.status = snapshot.status
  return patch
}

function patchHasChanges(patch: Record<string, unknown>) {
  return Object.keys(patch).some((k) => k !== 'expected_version')
}

function isVersionConflict(e: any) {
  return e?.response?.status === 409
    && e?.response?.data?.code === 'VERSION_CONFLICT'
}

async function persistNode(
  nodeId: number,
  snapshot: DirtySnapshot,
  attempt = 0,
): Promise<TaskNode> {
  const base = treeStore.byId.get(nodeId)
  if (!base) throw new Error('Task not found')

  const patch = buildPatch(base, snapshot)
  if (!patchHasChanges(patch)) {
    syncDirtyFromNode(base)
    return base
  }

  try {
    const updated = await treeStore.updateNode(nodeId, patch)
    syncDirtyFromNode(updated)
    return updated
  } catch (e: any) {
    if (isVersionConflict(e) && attempt < 1) {
      await treeStore.load(treeStore.groupId)
      if (!treeStore.byId.get(nodeId)) throw e
      applyDirtySnapshot(snapshot)
      return persistNode(nodeId, snapshot, attempt + 1)
    }
    throw e
  }
}

async function handleVersionConflict(nodeId: number, snapshot: DirtySnapshot) {
  try {
    await ElMessageBox.confirm(
      '该任务已被他人修改。将载入最新版本并保留你当前的编辑内容，是否继续保存？',
      '版本冲突',
      { confirmButtonText: '载入并保存', cancelButtonText: '取消' },
    )
  } catch {
    return false
  }
  try {
    await persistNode(nodeId, snapshot, 1)
    return true
  } catch (e: any) {
    if (isVersionConflict(e)) {
      ElMessage.error('仍有冲突，请关闭后重新打开任务再试')
      const fresh = treeStore.byId.get(nodeId)
      if (fresh) syncDirtyFromNode(fresh)
    } else {
      ElMessage.error(e?.response?.data?.message || '保存失败')
    }
    return false
  }
}

function saveErrorMessage(e: any): string {
  const msg = e?.response?.data?.message
  if (msg) return msg
  if (e?.response?.status === 409) return '保存失败，请刷新页面后重试'
  return '保存失败'
}

const saving = ref(false)
async function onSave() {
  const nodeId = props.node?.id
  if (!nodeId || !liveNode.value) return
  const snapshot = captureDirtySnapshot()
  saving.value = true
  try {
    await persistNode(nodeId, snapshot)
    ElMessage.success('保存成功')
    emit('update:visible', false)
  } catch (e: any) {
    if (isVersionConflict(e)) {
      const ok = await handleVersionConflict(nodeId, snapshot)
      if (ok) {
        ElMessage.success('已保存')
        emit('update:visible', false)
      }
    } else {
      ElMessage.error(saveErrorMessage(e))
    }
  } finally {
    saving.value = false
  }
}

const nudging = ref(false)
async function onNudge() {
  if (!props.node) return
  nudging.value = true
  try {
    await Api.nudge(treeStore.groupId, props.node.id)
    ElMessage.success('催办通知已发送')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '催办失败')
  } finally {
    nudging.value = false
  }
}

async function onDelete() {
  if (!props.node) return
  try {
    await ElMessageBox.confirm(
      `确认删除「${props.node.title}」？此操作会移除该节点及其全部子任务。`,
      '删除节点',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await treeStore.deleteNode(props.node.id)
    ElMessage.success('已删除')
    emit('update:visible', false)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

function handleClose(done: () => void) {
  if (isDirty.value) {
    ElMessageBox.confirm('有未保存的更改，确定关闭？', '提示', {
      confirmButtonText: '关闭',
      cancelButtonText: '继续编辑',
    })
      .then(() => done())
      .catch(() => {})
  } else {
    done()
  }
}

const loadingPosts = ref(false)
const relatedPosts = ref<PostBrief[]>([])
const relatedKeywords = ref<string[]>([])

const CATEGORY_LABELS: Record<string, string> = {
  template: '模板',
  case: '案例',
  tip: '干货',
  script: '话术',
  tool: '工具',
  link: '链接',
}

function categoryLabel(c: string) {
  return CATEGORY_LABELS[c] || c
}

async function loadRelatedPosts(taskId: number) {
  loadingPosts.value = true
  try {
    const r = await Api.relatedInspiration(treeStore.groupId, taskId)
    relatedPosts.value = r.items || []
    relatedKeywords.value = r.keywords || []
  } catch {
    relatedPosts.value = []
    relatedKeywords.value = []
  } finally {
    loadingPosts.value = false
  }
}

function goInspirationSearch() {
  const q = props.node?.title || relatedKeywords.value[relatedKeywords.value.length - 1] || ''
  router.push({ path: '/inspiration', query: q ? { q } : {} })
}

watch(
  () => props.node?.id,
  async (id) => {
    if (!id) return
    void loadTaskFiles(id)
    void loadTaskDiscussion(id)
    void loadRelatedPosts(id)
  },
)

function childProgressStyle(c: TaskNode) {
  if (c.status === 'done') {
    return { background: 'var(--color-success)' }
  }
  if (c.status === 'blocked') {
    return { background: 'var(--color-danger)' }
  }
  if (c.status === 'in_progress') {
    const p = taskBarPercent(c)
    return {
      background: `linear-gradient(to right, var(--color-primary) ${p}%, var(--bg-soft) ${p}%)`,
    }
  }
  return {}
}

function childProgressTitle(c: TaskNode) {
  const map: Record<string, string> = {
    todo: '待办',
    in_progress: '进行中',
    done: '已完成',
    blocked: '已阻塞',
  }
  return map[c.status] || c.status
}

function onAddChild() {
  if (!props.node) return
  emit('add-child', props.node.id)
}

function goPost(id: number) {
  router.push(`/inspiration/p/${id}`)
}

function goFiles() {
  if (!props.node) return
  router.push({
    path: `/groups/${route.params.gid}/files`,
    query: { view: 'tag', tag_task_id: String(props.node.id) },
  })
}

function goDiscussion(channelId?: number) {
  const q: Record<string, string> = {}
  if (channelId) q.channel = String(channelId)
  router.push({ path: `/groups/${route.params.gid}/discussion`, query: q })
}

const loadingFiles = ref(false)
const taskFiles = ref<FileInfo[]>([])

async function loadTaskFiles(taskId: number) {
  loadingFiles.value = true
  try {
    const list = await Api.listFiles(treeStore.groupId, { tag_task_id: taskId })
    taskFiles.value = (list || []).slice(0, 8)
  } catch {
    taskFiles.value = []
  } finally {
    loadingFiles.value = false
  }
}

function formatSize(n: number) {
  if (!n) return '0 B'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

const taskChannel = ref<Channel | null>(null)
const taskPreviewMessages = ref<DiscussionMessage[]>([])
const creatingTaskChannel = ref(false)

const DISC_PREVIEW_LIMIT = 3

function previewMessageBody(body: string, maxLen = 72) {
  const t = (body || '').replace(/\s+/g, ' ').trim()
  if (!t) return '（空消息）'
  return t.length > maxLen ? `${t.slice(0, maxLen)}…` : t
}

function isOwnPreviewMessage(m: DiscussionMessage) {
  return !!auth.user?.id && m.author_id === auth.user.id && !m.anon
}

async function loadTaskChannelPreview(channelId: number) {
  try {
    taskPreviewMessages.value = await Api.messages(treeStore.groupId, {
      channel_id: channelId,
      limit: DISC_PREVIEW_LIMIT,
    })
  } catch {
    taskPreviewMessages.value = []
  }
}

async function loadTaskDiscussion(taskId: number) {
  taskChannel.value = null
  taskPreviewMessages.value = []
  try {
    const channels = await Api.channels(treeStore.groupId)
    const found = channels.find((c) => c.task_id === taskId) || null
    taskChannel.value = found
    if (found) await loadTaskChannelPreview(found.id)
  } catch {
    taskChannel.value = null
    taskPreviewMessages.value = []
  }
}

async function createTaskChannel() {
  if (!props.node || taskChannel.value) return
  creatingTaskChannel.value = true
  try {
    taskChannel.value = await Api.getOrCreateTaskChannel(
      treeStore.groupId,
      props.node.id,
    )
    await loadTaskChannelPreview(taskChannel.value.id)
    ElMessage.success('任务讨论频道已创建')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    creatingTaskChannel.value = false
  }
}

function enterTaskDiscussion() {
  if (!taskChannel.value) return
  goDiscussion(taskChannel.value.id)
}

// AI suggest (mock)
const showAiSuggest = ref(false)
const aiSuggestions = computed(() => {
  // pick up to 3 members sorted by contribution as a simple heuristic
  return [...props.members]
    .filter((m) => !dirty.assignees.includes(m.user_id))
    .sort((a, b) => (b.contribution || 0) - (a.contribution || 0))
    .slice(0, 3)
    .map((m) => ({
      user_id: m.user_id,
      name: m.name,
      avatar_url: m.avatar_url,
      reason: m.skills?.length
        ? `技能匹配：${m.skills.slice(0, 2).join('、')}`
        : `贡献度高（${m.contribution || 0}）`,
    }))
})
function applySuggestion(uid: number) {
  if (!dirty.assignees.includes(uid)) dirty.assignees.push(uid)
  showAiSuggest.value = false
  ElMessage.success('已添加为负责人，请点击保存')
}
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
@use '@/styles/task-drawer.scss';
</style>

<style lang="scss" scoped>
.ai-suggest-list {
  list-style: none;
  padding: 0;
  margin: var(--space-3) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);

  li {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-3);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    background: var(--bg-soft);

    .s-name { font-weight: 600; font-size: var(--fs-sm); }
    .s-reason { flex: 1; font-size: var(--fs-xs); color: var(--text-tertiary); }
  }
}
</style>
