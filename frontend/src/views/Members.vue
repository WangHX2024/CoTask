<template>
  <div class="members-page">
    <!-- Header -->
    <div class="header-bar">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>&nbsp;返回
        </el-button>
        <div class="title-block">
          <h1 class="page-title">成员管理</h1>
          <div class="muted tiny">
            <template v-if="group">
              {{ group.course_name }} · {{ group.name }}
            </template>
          </div>
        </div>

        <!-- Invite code chip (leader) -->
        <div
          v-if="isLeader && group?.invite_code"
          class="invite-chip"
          @click="copyCode(group.invite_code!)"
        >
          <span class="chip-label">邀请码</span>
          <code class="chip-code">{{ group.invite_code }}</code>
          <el-icon class="copy-icon"><CopyDocument /></el-icon>
        </div>
      </div>

      <div class="header-right">
        <el-button
          v-if="isLeader"
          type="primary"
          @click="showInvite = true"
        >
          <el-icon><Plus /></el-icon>&nbsp;邀请新成员
        </el-button>
      </div>
    </div>

    <!-- Loading -->
    <template v-if="loading">
      <el-skeleton :rows="5" animated />
    </template>

    <!-- Empty -->
    <template v-else-if="members.length === 0">
      <el-empty description="还没有成员" />
    </template>

    <!-- List of member cards -->
    <ul v-else class="member-list">
      <li
        v-for="m in members"
        :key="m.user_id"
        class="member-row card"
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
              class="role-badge"
              :class="m.role === 'leader' ? 'role-leader' : 'role-member'"
            >
              {{ m.role === 'leader' ? '组长' : '组员' }}
            </span>
            <span v-if="m.user_id === selfId" class="self-tag">我</span>
          </div>
          <div class="m-meta muted tiny">
            <span v-if="isLeader && (m as any).phone">
              <el-icon><Phone /></el-icon> {{ (m as any).phone }}
            </span>
            <span>加入于 {{ formatJoin(m.joined_at) }}</span>
          </div>
        </div>

        <div class="m-contrib">
          <div class="contrib-num">{{ m.contribution }}</div>
          <div class="muted tiny">贡献分</div>
        </div>

        <div class="m-skills">
          <template v-if="m.skills?.length">
            <el-tag
              v-for="s in m.skills.slice(0, 4)"
              :key="s"
              size="small"
              effect="plain"
              class="skill-tag"
            >{{ s }}</el-tag>
            <span v-if="m.skills.length > 4" class="muted tiny">
              +{{ m.skills.length - 4 }}
            </span>
          </template>
          <span v-else class="muted tiny">暂无技能标签</span>
        </div>

        <div class="m-actions">
          <!-- Self row -->
          <template v-if="m.user_id === selfId">
            <el-button
              v-if="m.role === 'member'"
              size="small"
              type="danger"
              plain
              @click="onLeave"
            >退出小组</el-button>
            <span v-else class="muted tiny self-leader-note">
              组长需先转让
            </span>
          </template>

          <!-- Leader actions on others -->
          <template v-else-if="isLeader">
            <el-button
              size="small"
              @click="onTransfer(m)"
            >转让组长</el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="onKick(m)"
            >踢出小组</el-button>
          </template>
        </div>
      </li>
    </ul>

    <!-- Invite dialog -->
    <el-dialog
      v-model="showInvite"
      title="邀请新成员"
      width="440px"
      :close-on-click-modal="true"
    >
      <div class="invite-dialog">
        <div class="hint muted">
          将下方邀请码分享给同学，或让对方扫描二维码加入
        </div>

        <div class="big-code-block">
          <div class="big-code">{{ group?.invite_code || '--------' }}</div>
          <el-button
            v-if="group?.invite_code"
            type="primary"
            plain
            @click="copyCode(group.invite_code!)"
          >
            <el-icon><CopyDocument /></el-icon>&nbsp;复制邀请码
          </el-button>
        </div>

        <!-- QR placeholder -->
        <div class="qr-placeholder">
          <svg viewBox="0 0 100 100" class="qr-svg" aria-hidden="true">
            <rect x="0" y="0" width="100" height="100" fill="#fff" />
            <g fill="#1F2937">
              <!-- Corner squares -->
              <rect x="5" y="5" width="20" height="20" />
              <rect x="9" y="9" width="12" height="12" fill="#fff" />
              <rect x="12" y="12" width="6" height="6" />
              <rect x="75" y="5" width="20" height="20" />
              <rect x="79" y="9" width="12" height="12" fill="#fff" />
              <rect x="82" y="12" width="6" height="6" />
              <rect x="5" y="75" width="20" height="20" />
              <rect x="9" y="79" width="12" height="12" fill="#fff" />
              <rect x="12" y="82" width="6" height="6" />
              <!-- Dot pattern -->
              <rect x="30" y="10" width="4" height="4" />
              <rect x="40" y="10" width="4" height="4" />
              <rect x="50" y="10" width="4" height="4" />
              <rect x="60" y="10" width="4" height="4" />
              <rect x="30" y="30" width="4" height="4" />
              <rect x="40" y="30" width="4" height="4" />
              <rect x="50" y="30" width="4" height="4" />
              <rect x="60" y="30" width="4" height="4" />
              <rect x="70" y="30" width="4" height="4" />
              <rect x="30" y="50" width="4" height="4" />
              <rect x="50" y="50" width="4" height="4" />
              <rect x="70" y="50" width="4" height="4" />
              <rect x="30" y="70" width="4" height="4" />
              <rect x="40" y="70" width="4" height="4" />
              <rect x="50" y="70" width="4" height="4" />
              <rect x="60" y="70" width="4" height="4" />
              <rect x="70" y="70" width="4" height="4" />
              <rect x="80" y="35" width="4" height="4" />
              <rect x="85" y="45" width="4" height="4" />
              <rect x="35" y="40" width="4" height="4" />
              <rect x="45" y="55" width="4" height="4" />
              <rect x="55" y="60" width="4" height="4" />
              <rect x="65" y="65" width="4" height="4" />
            </g>
          </svg>
          <div class="qr-caption">扫码加入</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, CopyDocument, Plus, Phone,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { Api, type GroupBrief, type MemberInfo } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupsStore = useGroupsStore()

const gid = computed(() => Number(route.params.gid))
const selfId = computed(() => auth.user?.id || 0)

const loading = ref(true)
const group = ref<GroupBrief | null>(null)
const members = ref<MemberInfo[]>([])
const showInvite = ref(false)

const isLeader = computed(() => group.value?.role === 'leader')

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [g, list] = await Promise.all([
      Api.getGroup(gid.value),
      Api.members(gid.value),
    ])
    group.value = g
    // Sort: leader first, then by joined_at
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

async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('邀请码已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

function formatJoin(iso: string) {
  return dayjs(iso).format('YYYY-MM-DD')
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

<style lang="scss" scoped>
.members-page {
  max-width: 1080px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.title-block {
  display: flex;
  flex-direction: column;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.invite-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-soft);
  border: 1px dashed var(--border-color);
  border-radius: 999px;
  padding: 4px 12px;
  cursor: pointer;
  transition: background .12s;
  &:hover { background: var(--bg-card); }

  .chip-label { font-size: 11px; color: var(--text-tertiary); }
  .chip-code {
    font-family: SFMono-Regular, Menlo, Consolas, monospace;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: var(--text-primary);
  }
  .copy-icon { color: var(--color-primary); }
}

.member-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-row {
  display: grid;
  grid-template-columns: auto 1.5fr 90px 1.5fr auto;
  gap: 16px;
  align-items: center;
  padding: 14px 16px;
}
.m-info { min-width: 0; }
.m-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.m-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.role-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}
.role-leader {
  background: rgba(230,162,60,0.16);
  color: #B45309;
}
.role-member {
  background: rgba(61,126,255,0.14);
  color: #1D4ED8;
}
.self-tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: var(--bg-soft);
  color: var(--text-secondary);
}

.m-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  span { display: inline-flex; align-items: center; gap: 4px; }
}

.m-contrib {
  text-align: center;
  .contrib-num {
    font-size: 22px;
    font-weight: 700;
    color: var(--color-primary);
    line-height: 1;
  }
}

.m-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  .skill-tag { font-size: 11px; }
}

.m-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}
.self-leader-note {
  font-style: italic;
}

/* Invite dialog */
.invite-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  padding: 4px;

  .hint { text-align: center; }
}
.big-code-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: var(--bg-soft);
  border-radius: var(--radius-md);
  width: 100%;

  .big-code {
    font-family: SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 6px;
    color: var(--color-primary);
  }
}

.qr-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);

  .qr-svg {
    width: 160px;
    height: 160px;
    display: block;
  }
  .qr-caption {
    font-size: 12px;
    color: var(--text-secondary);
  }
}

@media (max-width: 760px) {
  .member-row {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "av info"
      "av meta"
      "contrib skills"
      "actions actions";
    gap: 8px 12px;
  }
  .m-avatar { grid-area: av; }
  .m-info { grid-area: info; }
  .m-contrib { grid-area: contrib; text-align: left; }
  .m-skills { grid-area: skills; }
  .m-actions { grid-area: actions; justify-content: flex-start; }

  .header-bar { flex-direction: column; align-items: stretch; }
  .header-left { flex-wrap: wrap; }
}
</style>
