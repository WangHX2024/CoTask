<template>
  <div class="members-page page insp-sub-page">
    <header class="insp-page-header">
      <div class="insp-page-header__lead">
        <button
          type="button"
          class="insp-capsule-btn insp-back-btn"
          aria-label="返回我的小组"
          @click="goBack"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <div class="page-header-text">
          <h1 class="page-title">成员管理</h1>
          <p v-if="group" class="page-desc">{{ group.course_name }} · {{ group.name }}</p>
        </div>
      </div>
      <div v-if="isLeader && group?.invite_code" class="insp-page-actions">
        <button
          type="button"
          class="insp-capsule-btn insp-capsule-btn--primary"
          @click="openInviteDialog"
        >
          <el-icon><Plus /></el-icon>
          <span>邀请成员</span>
        </button>
      </div>
    </header>

    <template v-if="loading">
      <div class="insp-panel members-skel">
        <el-skeleton :rows="5" animated />
      </div>
    </template>

    <template v-else-if="members.length === 0">
      <div class="insp-panel members-empty">
        <el-empty description="还没有成员" :image-size="100" />
      </div>
    </template>

    <ul v-else class="member-list insp-panel">
      <li
        v-for="m in members"
        :key="m.user_id"
        class="member-row"
      >
        <div class="m-avatar">
          <el-avatar :src="m.avatar_url || undefined" :size="48">
            {{ (m.name || '?').slice(0, 1) }}
          </el-avatar>
        </div>

        <div class="m-info">
          <div class="m-name-row">
            <span class="m-name">{{ m.name }}</span>
            <span
              class="insp-tag"
              :class="m.role === 'leader' ? 'insp-tag--leader' : 'insp-tag--member'"
            >
              {{ m.role === 'leader' ? '组长' : '组员' }}
            </span>
            <span v-if="m.user_id === selfId" class="insp-tag insp-tag--self">我</span>
          </div>
          <div class="m-meta muted tiny">
            <span v-if="isLeader && (m as any).phone" class="m-meta__phone">
              <el-icon><Phone /></el-icon>
              {{ (m as any).phone }}
            </span>
            <span>加入于 {{ formatJoin(m.joined_at) }}</span>
          </div>
        </div>

        <div class="m-skills">
          <template v-if="m.skills?.length">
            <span
              v-for="s in m.skills.slice(0, 4)"
              :key="s"
              class="skill-pill"
            >{{ s }}</span>
            <span v-if="m.skills.length > 4" class="muted tiny">
              +{{ m.skills.length - 4 }}
            </span>
          </template>
          <span v-else class="muted tiny">暂无技能标签</span>
        </div>

        <div class="m-actions">
          <template v-if="m.user_id === selfId">
            <button
              v-if="m.role === 'member'"
              type="button"
              class="insp-capsule-btn insp-capsule-btn--danger"
              @click="onLeave"
            >
              退出小组
            </button>
            <span v-else class="muted tiny self-leader-note">组长需先转让才可退出小组</span>
          </template>
          <template v-else-if="isLeader">
            <button type="button" class="insp-capsule-btn" @click="onTransfer(m)">
              转让组长
            </button>
            <button
              type="button"
              class="insp-capsule-btn insp-capsule-btn--danger"
              @click="onKick(m)"
            >
              踢出小组
            </button>
          </template>
        </div>
      </li>
    </ul>

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
            <div class="muted tiny">{{ group?.course_name }} · {{ group?.name }}</div>
          </div>
        </div>
      </template>

      <p class="invite-share__pitch">{{ invitePitchText }}</p>

      <div class="invite-share__code">
        <span class="invite-share__code-label">邀请码</span>
        <code class="invite-share__code-value">{{ group?.invite_code }}</code>
      </div>

      <template #footer>
        <div class="dialog-footer-actions">
          <button type="button" class="insp-capsule-btn" @click="showInviteShare = false">关闭</button>
          <button type="button" class="insp-capsule-btn" @click="copyInvitePitch">复制话术</button>
          <button
            type="button"
            class="insp-capsule-btn insp-capsule-btn--primary"
            @click="copyInviteCode"
          >
            复制邀请码
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Phone, Share } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/datetime'
import { Api, type GroupBrief, type MemberInfo } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import { buildGroupInvitePitch } from '@/utils/groupInvitePitch'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()

const gid = computed(() => Number(route.params.gid))
const selfId = computed(() => auth.user?.id || 0)

const loading = ref(true)
const group = ref<GroupBrief | null>(null)
const members = ref<MemberInfo[]>([])
const showInviteShare = ref(false)

const isLeader = computed(() => group.value?.role === 'leader')

const inviteSiteUrl = computed(() =>
  typeof window !== 'undefined' ? window.location.origin : '',
)

const invitePitchText = computed(() => {
  if (!group.value) return ''
  return buildGroupInvitePitch(group.value, inviteSiteUrl.value)
})

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [g, list] = await Promise.all([
      Api.getGroup(gid.value),
      Api.members(gid.value),
    ])
    group.value = g
    members.value = list.slice().sort((a, b) => {
      if (a.role !== b.role) return a.role === 'leader' ? -1 : 1
      return a.joined_at.localeCompare(b.joined_at)
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载成员失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/groups')
}

function openInviteDialog() {
  if (!group.value?.invite_code) return
  showInviteShare.value = true
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

async function copyInviteCode() {
  const code = group.value?.invite_code
  if (!code) return
  await copyText(code, '邀请码已复制')
}

function formatJoin(iso: string) {
  return formatDate(iso)
}

async function onTransfer(m: MemberInfo) {
  if (!group.value) return
  try {
    await ElMessageBox.confirm(
      `确定将组长转让给 "${m.name}" 吗？转让后你将变为普通成员。`,
      '转让组长',
      { type: 'warning', confirmButtonText: '转让', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await Api.transfer(gid.value, m.user_id)
    ElMessage.success(`已将组长转让给 ${m.name}`)
    await groupsStore.refresh()
    await loadAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '转让失败')
  }
}

async function onKick(m: MemberInfo) {
  try {
    await ElMessageBox.confirm(
      `确定将 "${m.name}" 踢出小组吗？该成员将无法继续访问小组内容。`,
      '踢出小组',
      { type: 'warning', confirmButtonText: '踢出', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await Api.kick(gid.value, m.user_id)
    ElMessage.success(`已将 ${m.name} 踢出小组`)
    await loadAll()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '踢出失败')
  }
}

async function onLeave() {
  if (!group.value) return
  try {
    await ElMessageBox.confirm(
      `确定要退出 "${group.value.name}" 吗？退出后将无法查看小组内容。`,
      '退出小组',
      { type: 'warning', confirmButtonText: '退出', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await Api.leaveGroup(gid.value)
    ElMessage.success('已退出小组')
    await groupsStore.refresh()
    router.push('/groups')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '退出失败')
  }
}
</script>

<style lang="scss">
@use '@/styles/inspiration-pages.scss';
</style>

<style lang="scss" scoped>
.members-skel,
.members-empty {
  padding: var(--space-6);
}

.member-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow: hidden;
  display: grid;
  /* Shared column tracks so skill tags align across rows */
  grid-template-columns: 52px minmax(160px, 240px) minmax(0, 1fr) auto;
  column-gap: var(--space-6);
}

.member-row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
  min-height: 80px;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
  transition: background 120ms ease;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--bg-soft);
  }
}

.m-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-1) 0;
}

.m-name-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.m-name {
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--text-primary);
}

.insp-tag--self {
  background: var(--bg-soft);
  color: var(--text-secondary);
}

.m-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.m-meta__phone {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.m-skills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  row-gap: var(--space-2);
  align-items: center;
  align-content: center;
  min-width: 0;
  padding: var(--space-1) 0;
  justify-content: flex-start;
}

.skill-pill {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: 500;
  background: var(--bg-soft);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.m-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  flex-wrap: wrap;
  padding-left: var(--space-2);
}

.self-leader-note {
  font-size: var(--fs-sm);
  white-space: nowrap;
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

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}

@media (max-width: 760px) {
  .member-list {
    display: block;
  }

  .member-row {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-4);
    min-height: 0;
    padding: var(--space-5) var(--space-4);
  }

  .m-skills,
  .m-actions {
    grid-column: 1 / -1;
  }

  .m-actions {
    justify-content: flex-start;
  }
}
</style>
