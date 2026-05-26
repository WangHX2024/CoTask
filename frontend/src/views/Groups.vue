<template>
  <div class="groups-page page insp-sub-page">
    <header class="insp-page-header">
      <div class="insp-page-header__lead">
        <div class="page-header-text">
          <h1 class="page-title">我的小组</h1>
          <p class="page-desc">管理和切换你参与的课程小组</p>
        </div>
      </div>
      <div class="insp-page-actions">
        <button type="button" class="insp-capsule-btn" @click="showJoin = true">
          <el-icon><Key /></el-icon>
          <span>加入小组</span>
        </button>
        <button type="button" class="insp-capsule-btn insp-capsule-btn--primary" @click="showCreate = true">
          <el-icon><Plus /></el-icon>
          <span>新建小组</span>
        </button>
      </div>
    </header>

    <!-- Filter tabs -->
    <div class="filter-bar">
      <SegmentedControl
        v-model="filter"
        size="md"
        :options="groupFilterOptions"
      />
    </div>

    <!-- Loading -->
    <template v-if="loading && !groupsStore.loaded">
      <div class="grid-skeleton">
        <el-skeleton v-for="i in 4" :key="i" :rows="5" animated />
      </div>
    </template>

    <!-- Empty state -->
    <template v-else-if="filteredGroups.length === 0">
      <el-empty
        :image-size="160"
        description="还没有小组，新建一个或加入一个吧"
      >
        <div class="empty-actions">
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            @click="showCreate = true"
          >
            <el-icon><Plus /></el-icon>
            <span>新建小组</span>
          </button>
          <button type="button" class="insp-capsule-btn" @click="showJoin = true">
            <el-icon><Key /></el-icon>
            <span>加入小组</span>
          </button>
        </div>
      </el-empty>
    </template>

    <!-- Card grid -->
    <div v-else class="cards-grid">
      <article
        v-for="g in filteredGroups"
        :key="g.id"
        class="group-card"
      >
        <div
          class="color-stripe"
          :style="{ '--stripe': stripeColor(g.course_name) }"
        ></div>

        <div class="card-body">
          <div class="card-head">
            <div class="head-titles">
              <div class="course-name">{{ g.course_name }}</div>
              <div class="group-name">{{ g.name }}</div>
            </div>
            <span
              class="insp-tag"
              :class="g.role === 'leader' ? 'insp-tag--leader' : 'insp-tag--member'"
            >
              {{ g.role === 'leader' ? '组长' : '组员' }}
            </span>
          </div>

          <div class="desc-slot">
            <p v-if="g.description" class="desc">{{ g.description }}</p>
          </div>

          <div class="member-stack">
            <MemberAvatars :group-id="g.id" :count="g.member_count" />
          </div>

          <div class="progress-block">
            <el-progress
              :percentage="Math.round(g.progress || 0)"
              :stroke-width="8"
              :show-text="false"
              :color="progressColor(g.progress)"
            />
            <div class="stats-row">
              <span class="muted tiny">成员 {{ g.member_count }} 人</span>
              <span class="muted tiny">进度 {{ Math.round(g.progress || 0) }}%</span>
            </div>
          </div>

          <div
            class="invite-slot"
            :class="{ 'invite-slot--has': g.role === 'leader' && g.status === 'active' && g.invite_code }"
          >
            <div
              v-if="g.role === 'leader' && g.status === 'active' && g.invite_code"
              class="invite-row"
              @click.stop="openInviteDialog(g)"
            >
              <span class="invite-label">邀请码</span>
              <code class="invite-code">{{ g.invite_code }}</code>
              <el-icon class="copy-icon"><CopyDocument /></el-icon>
            </div>
          </div>

          <div class="card-actions">
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--primary"
              @click="enterGroup(g)"
            >
              进入
            </button>
            <button type="button" class="insp-capsule-btn" @click="manageMembers(g)">
              成员管理
            </button>
            <el-dropdown trigger="click" @command="(c: string) => onDropdown(c, g)">
              <button type="button" class="insp-capsule-btn insp-capsule-btn--icon">
                <el-icon><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-if="g.role === 'member'"
                    command="leave"
                  >退出小组</el-dropdown-item>
                  <el-dropdown-item
                    v-if="g.role === 'leader'"
                    command="dissolve"
                  >
                    <span class="danger-text">解散小组</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </article>
    </div>

    <!-- Create dialog -->
    <el-dialog
      v-model="showCreate"
      class="sub-page-dialog"
      title="新建小组"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-position="top"
      >
        <el-form-item label="课程名" prop="course_name">
          <el-input
            v-model="createForm.course_name"
            class="insp-capsule-input"
            placeholder="如：软件工程"
            maxlength="40"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="小组名" prop="name">
          <el-input
            v-model="createForm.name"
            class="insp-capsule-input"
            placeholder="给小组起个名字"
            maxlength="40"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            class="insp-capsule-textarea"
            type="textarea"
            :rows="3"
            placeholder="小组介绍（选填）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer-actions">
          <button type="button" class="insp-capsule-btn" @click="showCreate = false">取消</button>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            :disabled="creating"
            @click="onCreate"
          >
            {{ creating ? '创建中…' : '创建' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- Join dialog -->
    <el-dialog
      v-model="showJoin"
      class="sub-page-dialog"
      title="加入小组"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="joinFormRef"
        :model="joinForm"
        :rules="joinRules"
        label-position="top"
      >
        <el-form-item label="邀请码" prop="invite_code">
          <el-input
            v-model="joinForm.invite_code"
            class="insp-capsule-input invite-input"
            placeholder="邀请码（8位）"
            maxlength="8"
            @input="onInviteInput"
          />
        </el-form-item>
        <div class="hint tiny muted">向组长索取邀请码后填入</div>
      </el-form>
      <template #footer>
        <div class="dialog-footer-actions">
          <button type="button" class="insp-capsule-btn" @click="showJoin = false">取消</button>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            :disabled="joining"
            @click="onJoin"
          >
            {{ joining ? '加入中…' : '加入' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showInviteShare"
      class="sub-page-dialog invite-share-dialog"
      width="min(480px, 92vw)"
      :close-on-click-modal="true"
    >
      <template #header>
        <div class="invite-share__head">
          <el-icon class="invite-share__icon"><Share /></el-icon>
          <div>
            <div class="invite-share__title">邀请成员</div>
            <div class="muted tiny">{{ inviteTarget?.course_name }} · {{ inviteTarget?.name }}</div>
          </div>
        </div>
      </template>

      <p class="invite-share__pitch">{{ invitePitchText }}</p>

      <div class="invite-share__code">
        <span class="invite-share__code-label">邀请码</span>
        <code class="invite-share__code-value">{{ inviteTarget?.invite_code }}</code>
      </div>

      <template #footer>
        <div class="dialog-footer-actions">
          <button type="button" class="insp-capsule-btn" @click="showInviteShare = false">关闭</button>
          <button type="button" class="insp-capsule-btn" @click="copyInvitePitch">复制话术</button>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            @click="copyInviteCodeFromDialog"
          >
            复制邀请码
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, h, defineComponent } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { CopyDocument, MoreFilled, Key, Plus, Share } from '@element-plus/icons-vue'
import { Api, type GroupBrief, type MemberInfo } from '@/api'
import { useGroupsStore } from '@/stores/groups'
import SegmentedControl from '@/components/common/SegmentedControl.vue'
import { buildGroupInvitePitch } from '@/utils/groupInvitePitch'

const groupFilterOptions = [
  { label: '全部', value: 'all' as const },
  { label: '我是组长', value: 'leader' as const },
  { label: '我是组员', value: 'member' as const },
]

const router = useRouter()
const groupsStore = useGroupsStore()

// ---------- state ----------
const loading = ref(false)
const filter = ref<'all' | 'leader' | 'member'>('all')

const showCreate = ref(false)
const showJoin = ref(false)
const inviteTarget = ref<GroupBrief | null>(null)

const showInviteShare = computed({
  get: () => inviteTarget.value !== null,
  set: (open: boolean) => {
    if (!open) inviteTarget.value = null
  },
})

const inviteSiteUrl = computed(() =>
  typeof window !== 'undefined' ? window.location.origin : '',
)

const invitePitchText = computed(() => {
  const g = inviteTarget.value
  if (!g) return ''
  return buildGroupInvitePitch(g, inviteSiteUrl.value)
})
const creating = ref(false)
const joining = ref(false)

const createFormRef = ref<FormInstance>()
const joinFormRef = ref<FormInstance>()

const createForm = ref({
  course_name: '',
  name: '',
  description: '',
})
const joinForm = ref({
  invite_code: '',
})

const createRules: FormRules = {
  course_name: [{ required: true, message: '请填写课程名', trigger: 'blur' }],
  name: [{ required: true, message: '请填写小组名', trigger: 'blur' }],
}
const joinRules: FormRules = {
  invite_code: [
    { required: true, message: '请填写邀请码', trigger: 'blur' },
    { len: 8, message: '邀请码为 8 位', trigger: 'blur' },
  ],
}

// ---------- load ----------
onMounted(async () => {
  loading.value = true
  try {
    await groupsStore.refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载小组失败')
  } finally {
    loading.value = false
  }
})

// ---------- derived ----------
const filteredGroups = computed<GroupBrief[]>(() => {
  const list = groupsStore.list
  if (filter.value === 'all') return list
  return list.filter((g) => g.role === filter.value)
})

// ---------- actions ----------
async function onCreate() {
  if (!createFormRef.value) return
  const ok = await createFormRef.value.validate().catch(() => false)
  if (!ok) return
  creating.value = true
  try {
    await groupsStore.create({
      course_name: createForm.value.course_name.trim(),
      name: createForm.value.name.trim(),
      description: createForm.value.description.trim() || undefined,
    })
    ElMessage.success('小组已创建')
    showCreate.value = false
    createForm.value = { course_name: '', name: '', description: '' }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

function onInviteInput(v: string) {
  joinForm.value.invite_code = v.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8)
}

async function onJoin() {
  if (!joinFormRef.value) return
  const ok = await joinFormRef.value.validate().catch(() => false)
  if (!ok) return
  joining.value = true
  try {
    const g = await groupsStore.join(joinForm.value.invite_code)
    ElMessage.success(`已加入 ${g.name}`)
    showJoin.value = false
    joinForm.value.invite_code = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加入失败')
  } finally {
    joining.value = false
  }
}

function enterGroup(g: GroupBrief) {
  groupsStore.setCurrent(g.id)
  router.push(`/groups/${g.id}/tree`)
}
function manageMembers(g: GroupBrief) {
  groupsStore.setCurrent(g.id)
  router.push(`/groups/${g.id}/members`)
}

function openInviteDialog(g: GroupBrief) {
  if (g.role !== 'leader' || g.status !== 'active' || !g.invite_code) return
  inviteTarget.value = g
}

async function copyText(text: string, okMsg: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(okMsg)
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

async function copyInvitePitch() {
  if (!invitePitchText.value) return
  await copyText(invitePitchText.value, '邀请话术已复制')
}

async function copyInviteCodeFromDialog() {
  const code = inviteTarget.value?.invite_code
  if (!code) return
  await copyText(code, '邀请码已复制')
}

function onDropdown(cmd: string, g: GroupBrief) {
  if (cmd === 'leave') return onLeave(g)
  if (cmd === 'dissolve') return onDissolve(g)
}

async function onLeave(g: GroupBrief) {
  try {
    await ElMessageBox.confirm(
      `确定要退出 "${g.name}" 吗？退出后将无法查看小组内容。`,
      '退出小组',
      { type: 'warning', confirmButtonText: '退出', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await Api.leaveGroup(g.id)
    ElMessage.success('已退出小组')
    await groupsStore.refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '退出失败')
  }
}

async function onDissolve(g: GroupBrief) {
  try {
    const { value } = await ElMessageBox.prompt(
      `解散后小组将被删除，无法恢复。请输入小组名 "${g.name}" 以确认：`,
      '解散小组',
      {
        confirmButtonText: '解散',
        cancelButtonText: '取消',
        type: 'error',
        inputValidator: (val) => val === g.name || '小组名不一致',
      },
    )
    if (value !== g.name) return
  } catch {
    return
  }
  try {
    await Api.dissolveGroup(g.id, g.name)
    ElMessage.success('小组已解散')
    await groupsStore.refresh()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '解散失败')
  }
}

// ---------- helpers ----------
const palette = [
  '#3D7EFF', '#F56C6C', '#67C23A', '#E6A23C',
  '#9F7AEA', '#14B8A6', '#EC4899', '#6366F1',
]
function hashStr(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0
  return Math.abs(h)
}
function stripeColor(name: string) {
  return palette[hashStr(name || '?') % palette.length]
}
function progressColor(p: number) {
  if (p >= 80) return '#67C23A'
  if (p >= 40) return '#3D7EFF'
  return '#E6A23C'
}

// ---------- Member avatar stack (async fetch) ----------
const MemberAvatars = defineComponent({
  props: {
    groupId: { type: Number, required: true },
    count: { type: Number, default: 0 },
  },
  setup(props) {
    const members = ref<MemberInfo[]>([])
    const loaded = ref(false)
    const fetchMembers = async () => {
      try {
        members.value = await Api.members(props.groupId)
      } catch {
        // ignore
      } finally {
        loaded.value = true
      }
    }
    onMounted(fetchMembers)

    return () => {
      const shown = members.value.slice(0, 4)
      const more = Math.max(0, (props.count || members.value.length) - shown.length)
      return h('div', { class: 'avatar-stack' }, [
        ...shown.map((m) =>
          h('div', { class: 'av', key: m.user_id, title: m.name }, [
            m.avatar_url
              ? h('img', { src: m.avatar_url, alt: m.name })
              : h('span', { class: 'av-fallback' }, (m.name || '?').slice(0, 1)),
          ]),
        ),
        more > 0
          ? h('div', { class: 'av av-more', key: 'more' }, `+${more}`)
          : null,
      ])
    }
  },
})
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.filter-bar {
  display: flex;
  justify-content: flex-start;
}

.empty-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: center;
  flex-wrap: wrap;
}

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.grid-skeleton,
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-6);
  align-items: stretch;
}

.grid-skeleton :deep(.el-skeleton) {
  padding: var(--space-6);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.group-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-shadow: none;
  transition: border-color 150ms ease, box-shadow 150ms ease;

  &:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-sm);
  }
}

.color-stripe {
  --stripe: var(--color-primary);
  height: 5px;
  width: 100%;
  flex-shrink: 0;
  background: linear-gradient(
    90deg,
    var(--stripe) 0%,
    color-mix(in srgb, var(--stripe) 55%, transparent) 55%,
    transparent 100%
  );
  opacity: 0.92;
}

.card-body {
  padding: var(--space-5);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 0;
}

/* Head: course + group name + role badge */
.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.head-titles {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.course-name,
.group-name,
.desc {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-name {
  font-size: var(--fs-sm);
  line-height: 1.35;
  min-height: calc(var(--fs-sm) * 1.35);
  color: var(--text-tertiary);
}

.group-name {
  font-size: var(--fs-lg);
  font-weight: 700;
  line-height: 1.3;
  min-height: calc(var(--fs-lg) * 1.3);
  color: var(--text-primary);
}

.desc-slot {
  min-height: calc(var(--fs-xs) * 1.35);
  display: flex;
  align-items: center;
}

.desc {
  width: 100%;
  font-size: var(--fs-xs);
  line-height: 1.35;
  color: var(--text-secondary);
}

.member-stack {
  display: flex;
  align-items: center;
  min-height: 28px;
}

.invite-slot {
  min-height: 0;
  display: flex;
  align-items: center;

  &--has {
    min-height: 32px;
  }
}

/* Avatar stack (overlapping circles) */
:deep(.avatar-stack) {
  display: flex;
  align-items: center;

  .av {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid var(--bg-card);
    background: var(--bg-soft);
    margin-left: -8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--text-secondary);

    &:first-child { margin-left: 0; }
    img { width: 100%; height: 100%; object-fit: cover; }
  }

  .av-more {
    background: var(--bg-soft);
    color: var(--text-tertiary);
    font-size: var(--fs-xs);
  }
}

/* Progress block */
.progress-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stats-row {
  display: flex;
  justify-content: space-between;
}

.invite-row {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  align-self: flex-start;
  background: var(--bg-soft);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  padding: var(--space-1) var(--space-3);
  cursor: pointer;
  transition: background 120ms ease, border-color 120ms ease;

  &:hover {
    background: var(--color-primary-light);
    border-color: transparent;
  }

  .invite-label { font-size: var(--fs-xs); color: var(--text-tertiary); }

  .invite-code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: var(--fs-base);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 1px;
  }

  .copy-icon { font-size: var(--fs-base); color: var(--color-primary); }
}

.card-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.invite-share__head {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.invite-share__icon {
  font-size: 22px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.invite-share__title {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.invite-share__pitch {
  margin: 0 0 var(--space-4);
  padding: var(--space-4);
  background: var(--bg-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  font-size: var(--fs-base);
  line-height: 1.65;
  color: var(--text-primary);
  white-space: pre-line;
}

.invite-share__code {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: var(--bg-card);
}

.invite-share__code-label {
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.invite-share__code-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: var(--fs-lg);
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--color-primary);
}

.danger-text { color: var(--color-danger); }

/* Join dialog: monospace big code input */
.invite-input :deep(input) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 4px;
  font-size: 18px;
  text-align: center;
  font-weight: 700;
}

.hint { color: var(--text-tertiary); }

/* Responsive */
@media (max-width: 640px) {
  .cards-grid { grid-template-columns: 1fr; }
}
</style>
