<template>
  <div class="groups-page">
    <!-- Header strip -->
    <div class="header-strip">
      <h1 class="page-title">我的小组</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreate = true">
          <span class="btn-icon">+</span>&nbsp;新建小组
        </el-button>
        <el-button type="warning" @click="showJoin = true">
          <span class="btn-icon">🔑</span>&nbsp;加入小组
        </el-button>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="filter-bar">
      <el-radio-group v-model="filter" size="default">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="leader">我是组长</el-radio-button>
        <el-radio-button label="member">我是组员</el-radio-button>
      </el-radio-group>
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
          <el-button type="primary" @click="showCreate = true">
            + 新建小组
          </el-button>
          <el-button type="warning" @click="showJoin = true">
            🔑 加入小组
          </el-button>
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
          :style="{ background: stripeColor(g.course_name) }"
        ></div>

        <div class="card-body">
          <div class="card-head">
            <div class="head-titles">
              <div class="course-name">{{ g.course_name }}</div>
              <div class="group-name">{{ g.name }}</div>
            </div>
            <span
              class="role-badge"
              :class="g.role === 'leader' ? 'role-leader' : 'role-member'"
            >
              {{ g.role === 'leader' ? '组长' : '组员' }}
            </span>
          </div>

          <p v-if="g.description" class="desc">{{ g.description }}</p>

          <!-- Member avatars -->
          <div class="member-stack">
            <MemberAvatars :group-id="g.id" :count="g.member_count" />
          </div>

          <!-- Progress -->
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

          <!-- Invite code (leader + active) -->
          <div
            v-if="g.role === 'leader' && g.status === 'active' && g.invite_code"
            class="invite-row"
            @click.stop="copyCode(g.invite_code!)"
          >
            <span class="invite-label">邀请码</span>
            <code class="invite-code">{{ g.invite_code }}</code>
            <el-icon class="copy-icon"><CopyDocument /></el-icon>
          </div>

          <!-- Hover actions -->
          <div class="hover-actions">
            <el-button size="small" type="primary" @click="enterGroup(g)">
              进入
            </el-button>
            <el-button size="small" @click="manageMembers(g)">
              成员管理
            </el-button>
            <el-dropdown trigger="click" @command="(c: string) => onDropdown(c, g)">
              <el-button size="small" circle>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-if="g.role === 'member'"
                    command="leave"
                  >退出小组</el-dropdown-item>
                  <el-dropdown-item
                    v-if="g.role === 'leader'"
                    command="dissolve"
                    divided
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
            placeholder="如：软件工程"
            maxlength="40"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="小组名" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="给小组起个名字"
            maxlength="40"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="小组介绍（选填）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Join dialog -->
    <el-dialog
      v-model="showJoin"
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
            placeholder="8 位邀请码"
            maxlength="8"
            class="invite-input"
            @input="onInviteInput"
          />
        </el-form-item>
        <div class="hint tiny muted">向组长索取邀请码后填入</div>
      </el-form>
      <template #footer>
        <el-button @click="showJoin = false">取消</el-button>
        <el-button type="primary" :loading="joining" @click="onJoin">
          加入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, h, defineComponent } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { CopyDocument, MoreFilled } from '@element-plus/icons-vue'
import { Api, type GroupBrief, type MemberInfo } from '@/api'
import { useGroupsStore } from '@/stores/groups'

const router = useRouter()
const groupsStore = useGroupsStore()

// ---------- state ----------
const loading = ref(false)
const filter = ref<'all' | 'leader' | 'member'>('all')

const showCreate = ref(false)
const showJoin = ref(false)
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

async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('邀请码已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
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
  const c = palette[hashStr(name || '?') % palette.length]
  return `linear-gradient(90deg, ${c}, ${c}aa)`
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

<style lang="scss" scoped>
.groups-page {
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.header-actions {
  display: flex;
  gap: 8px;
}
.btn-icon { font-weight: 700; }

.filter-bar {
  display: flex;
  justify-content: flex-start;
}

.empty-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.grid-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.group-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 280px;
  transition: transform .15s ease, box-shadow .15s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);

    .hover-actions { opacity: 1; transform: translateY(0); }
  }
}

.color-stripe {
  height: 6px;
  width: 100%;
}

.card-body {
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.head-titles { min-width: 0; flex: 1; }
.course-name {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.group-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.role-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.role-leader {
  background: rgba(230,162,60,0.16);
  color: #B45309;
}
.role-member {
  background: rgba(61,126,255,0.14);
  color: #1D4ED8;
}

.desc {
  margin: 0;
  font-size: 12.5px;
  color: var(--text-secondary);
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

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
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);

    &:first-child { margin-left: 0; }
    img { width: 100%; height: 100%; object-fit: cover; }
  }
  .av-more {
    background: var(--bg-soft);
    color: var(--text-tertiary);
    font-size: 11px;
  }
}

.progress-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: auto;
}
.stats-row {
  display: flex;
  justify-content: space-between;
}

.invite-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-soft);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  cursor: pointer;
  transition: background .12s;
  &:hover { background: var(--bg-page); }

  .invite-label {
    font-size: 11px;
    color: var(--text-tertiary);
  }
  .invite-code {
    font-family: SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.5px;
  }
  .copy-icon {
    font-size: 13px;
    color: var(--color-primary);
  }
}

.hover-actions {
  position: absolute;
  right: 12px;
  bottom: 12px;
  display: flex;
  gap: 6px;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity .15s, transform .15s;
}
.danger-text { color: var(--color-danger); }

.invite-input :deep(input) {
  font-family: SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 4px;
  font-size: 18px;
  text-align: center;
  font-weight: 700;
}

.hint { margin-top: -8px; }

@media (max-width: 640px) {
  .header-strip { flex-direction: column; align-items: flex-start; }
  .cards-grid { grid-template-columns: 1fr; }
  .hover-actions {
    position: static;
    opacity: 1;
    transform: none;
    margin-top: 8px;
  }
}
</style>
