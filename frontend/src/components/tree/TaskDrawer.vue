<template>
  <el-drawer
    :model-value="visible"
    :with-header="false"
    direction="rtl"
    size="480px"
    :destroy-on-close="false"
    :before-close="handleClose"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
  >
    <div v-if="node" class="td">
      <!-- Header -->
      <div class="td-head">
        <div class="td-head-top">
          <span class="status-dot" :class="`dot-${dirty.status}`"></span>
          <div class="title-wrap">
            <el-input
              v-if="canEdit"
              v-model="dirty.title"
              :placeholder="'任务标题'"
              size="large"
              class="title-input"
              :input-style="{ fontSize: '18px', fontWeight: '600' }"
            />
            <div v-else class="title-readonly">{{ dirty.title }}</div>
          </div>
          <el-button text @click="emit('update:visible', false)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <div class="td-head-meta">
          <el-select
            v-model="dirty.status"
            size="small"
            style="width: 130px"
            :disabled="!canChangeStatus"
          >
            <el-option value="todo" label="待办" />
            <el-option value="in_progress" label="进行中" />
            <el-option value="done" label="已完成" />
            <el-option value="blocked" label="已阻塞" />
          </el-select>

          <el-date-picker
            v-if="node.is_leaf"
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="→"
            start-placeholder="开始"
            end-placeholder="DDL"
            size="small"
            style="width: 240px"
            :disabled="!canEdit"
          />
          <span v-else class="tiny muted">复合任务（无 DDL）</span>
        </div>
      </div>

      <el-divider />

      <!-- Assignees -->
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">负责人</span>
          <el-button
            v-if="canEdit"
            size="small"
            text
            type="primary"
            @click="showAiSuggest = true"
          >
            <el-icon><MagicStick /></el-icon>&nbsp;AI 建议负责人
          </el-button>
        </div>
        <div class="assign-row">
          <el-tooltip
            v-for="uid in dirty.assignees"
            :key="uid"
            :content="memberMap.get(uid)?.name || '未知用户'"
            placement="top"
          >
            <span class="assign-chip">
              <el-avatar :size="24" :src="memberMap.get(uid)?.avatar_url">
                {{ (memberMap.get(uid)?.name || '?').slice(0, 1) }}
              </el-avatar>
              <span class="chip-name">{{ memberMap.get(uid)?.name || '?' }}</span>
              <el-icon v-if="canEdit" class="chip-x" @click="removeAssignee(uid)"><Close /></el-icon>
            </span>
          </el-tooltip>
          <el-popover
            v-if="canEdit"
            trigger="click"
            placement="bottom-start"
            :width="280"
          >
            <template #reference>
              <el-button size="small" circle>
                <el-icon><Plus /></el-icon>
              </el-button>
            </template>
            <el-select
              v-model="dirty.assignees"
              multiple
              filterable
              placeholder="选择成员"
              style="width: 100%"
            >
              <el-option
                v-for="m in members"
                :key="m.user_id"
                :value="m.user_id"
                :label="m.name"
              />
            </el-select>
          </el-popover>
          <span v-if="!dirty.assignees.length" class="tiny muted">未指派任何成员</span>
        </div>
      </section>

      <!-- Description -->
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">描述</span>
        </div>
        <el-input
          v-model="dirty.description"
          type="textarea"
          :rows="4"
          placeholder="补充任务描述、目标、产出标准…"
          :disabled="!canEdit"
        />
      </section>

      <!-- Dependencies -->
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">前置依赖</span>
        </div>
        <el-select
          v-model="dirty.dependencies"
          multiple
          filterable
          placeholder="选择前置任务"
          style="width: 100%"
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
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">子任务 ({{ children.length }})</span>
        </div>
        <ul v-if="children.length" class="child-list">
          <li
            v-for="c in children"
            :key="c.id"
            class="child-row"
            @click="emit('select', c.id)"
          >
            <span class="status-dot" :class="`dot-${c.status}`"></span>
            <span class="child-title">{{ c.title }}</span>
            <span class="child-prog tiny muted">{{ Math.round(c.progress) }}%</span>
          </li>
        </ul>
        <el-empty v-else description="暂无子任务" :image-size="64" />
      </section>

      <!-- Files -->
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">附件</span>
          <el-button size="small" text @click="goFiles">前往文件页</el-button>
        </div>
        <el-empty description="暂无附件" :image-size="64">
          <el-button size="small" disabled>
            <el-icon><Plus /></el-icon>&nbsp;上传
          </el-button>
        </el-empty>
      </section>

      <!-- Related inspirations -->
      <section class="td-section">
        <div class="section-head">
          <span class="section-title">相关灵感</span>
        </div>
        <el-skeleton v-if="loadingPosts" :rows="2" animated />
        <ul v-else-if="relatedPosts.length" class="post-list">
          <li v-for="p in relatedPosts" :key="p.id" class="post-row" @click="goPost(p.id)">
            <div class="post-title">{{ p.title }}</div>
            <div class="post-ex tiny muted">{{ p.excerpt }}</div>
          </li>
        </ul>
        <el-empty v-else description="暂无相关灵感" :image-size="64" />
      </section>

      <!-- Discussion -->
      <section class="td-section">
        <el-collapse>
          <el-collapse-item title="讨论（0）" name="d">
            <el-input
              type="textarea"
              :rows="2"
              placeholder="留言（演示，请前往讨论区）"
              disabled
            />
            <div class="discussion-empty muted tiny">
              暂无讨论。
              <el-button size="small" text type="primary" @click="goDiscussion">前往讨论区</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </section>

      <!-- Footer -->
      <footer class="td-foot">
        <el-button
          v-if="canNudge"
          type="warning"
          plain
          :loading="nudging"
          @click="onNudge"
        >
          <el-icon><Bell /></el-icon>&nbsp;催办
        </el-button>
        <el-button
          v-if="canEdit"
          type="danger"
          plain
          @click="onDelete"
        >
          <el-icon><Delete /></el-icon>&nbsp;删除
        </el-button>
        <span class="grow"></span>
        <el-button @click="emit('update:visible', false)">关闭</el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="!isDirty"
          @click="onSave"
        >
          保存
        </el-button>
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
import { computed, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Plus, Delete, Bell, MagicStick } from '@element-plus/icons-vue'
import { Api, type TaskNode, type MemberInfo, type PostBrief } from '@/api'
import { useTreeStore } from '@/stores/tree'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  visible: boolean
  node: TaskNode | null
  members: MemberInfo[]
  currentRole: 'leader' | 'member' | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'select', id: number): void
}>()

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const treeStore = useTreeStore()

const canEdit = computed(() => props.currentRole === 'leader')
const canChangeStatus = computed(() => {
  if (canEdit.value) return true
  // members can change status of tasks they're assigned to
  return !!props.node && (props.node.assignees || []).includes(auth.user?.id || 0)
})
const canNudge = computed(() => {
  if (canEdit.value) return true
  return !!props.node && (props.node.assignees || []).includes(auth.user?.id || 0)
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

watch(
  () => props.node?.id,
  (id) => {
    if (!id || !props.node) return
    dirty.title = props.node.title
    dirty.description = props.node.description || ''
    dirty.status = props.node.status
    dirty.assignees = [...(props.node.assignees || [])]
    dirty.dependencies = [...(props.node.dependencies || [])]
    dirty.start_date = props.node.start_date || ''
    dirty.end_date = props.node.end_date || ''
  },
  { immediate: true },
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

const dependableNodes = computed<TaskNode[]>(() =>
  treeStore.nodes.filter((n) => props.node && n.id !== props.node.id),
)

const isDirty = computed(() => {
  if (!props.node) return false
  return (
    dirty.title !== props.node.title ||
    dirty.description !== (props.node.description || '') ||
    dirty.status !== props.node.status ||
    !sameArr(dirty.assignees, props.node.assignees || []) ||
    !sameArr(dirty.dependencies, props.node.dependencies || []) ||
    dirty.start_date !== (props.node.start_date || '') ||
    dirty.end_date !== (props.node.end_date || '')
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

const saving = ref(false)
async function onSave() {
  if (!props.node) return
  saving.value = true
  try {
    const patch: any = {}
    if (dirty.title !== props.node.title) patch.title = dirty.title
    if (dirty.description !== (props.node.description || '')) patch.description = dirty.description
    if (dirty.status !== props.node.status) patch.status = dirty.status
    if (!sameArr(dirty.assignees, props.node.assignees || [])) patch.assignees = dirty.assignees
    if (!sameArr(dirty.dependencies, props.node.dependencies || []))
      patch.dependencies = dirty.dependencies
    if (dirty.start_date !== (props.node.start_date || ''))
      patch.start_date = dirty.start_date || null
    if (dirty.end_date !== (props.node.end_date || '')) patch.end_date = dirty.end_date || null
    patch.expected_version = props.node.version
    await treeStore.updateNode(props.node.id, patch)
    ElMessage.success('保存成功')
  } catch (e: any) {
    if (e?.response?.status === 409) {
      try {
        await ElMessageBox.confirm(
          '该任务已被他人修改，是否重新载入最新版本？',
          '版本冲突',
          { confirmButtonText: '重新载入', cancelButtonText: '继续编辑' },
        )
        await treeStore.load(treeStore.groupId)
      } catch {
        // user cancelled
      }
    } else {
      ElMessage.error(e?.response?.data?.message || '保存失败')
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

// related posts
const loadingPosts = ref(false)
const relatedPosts = ref<PostBrief[]>([])
watch(
  () => props.node?.id,
  async (id) => {
    if (!id) return
    loadingPosts.value = true
    try {
      const r = await Api.posts({ category: 'case', page: 1, size: 3 })
      relatedPosts.value = r.items || []
    } catch {
      relatedPosts.value = []
    } finally {
      loadingPosts.value = false
    }
  },
)

function goPost(id: number) {
  router.push(`/inspiration/p/${id}`)
}
function goFiles() {
  router.push(`/groups/${route.params.gid}/files`)
}
function goDiscussion() {
  router.push(`/groups/${route.params.gid}/discussion`)
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
  ElMessage.success('已添加为负责人，请保存')
}
</script>

<style lang="scss" scoped>
.td {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 20px 80px 20px;
  position: relative;
}

.td-head {
  position: sticky;
  top: 0;
  background: var(--bg-card);
  padding-top: 20px;
  z-index: 2;
}
.td-head-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-wrap {
  flex: 1;
  min-width: 0;
}
.title-input :deep(.el-input__wrapper) {
  box-shadow: none;
  padding: 0;
  background: transparent;
}
.title-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--color-primary);
  padding: 0 6px;
}
.title-readonly {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}

.td-head-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  flex-wrap: wrap;
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

.td-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.assign-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.assign-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px 2px 2px;
  background: var(--bg-soft);
  border-radius: var(--radius-full);
  font-size: 12px;
  .chip-name { padding: 0 4px; }
  .chip-x {
    cursor: pointer;
    font-size: 12px;
    color: var(--text-tertiary);
    &:hover { color: var(--color-danger); }
  }
}

.child-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}
.child-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  &:hover { background: var(--bg-soft); }
  .child-title { flex: 1; min-width: 0; }
}

.post-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.post-row {
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  &:hover { border-color: var(--color-primary); }
  .post-title { font-weight: 500; font-size: 13px; margin-bottom: 2px; }
  .post-ex {
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
}

.discussion-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.td-foot {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  padding: 12px 20px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 3;
}
.grow { flex: 1; }

.ai-suggest-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    .s-name { font-weight: 500; }
    .s-reason { flex: 1; }
  }
}
</style>
