<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: ui.sidebarCollapsed }">
      <div class="logo-row">
        <div class="logo">
          <span class="logo-mark">Co</span>
          <span v-if="!ui.sidebarCollapsed" class="logo-text">Task</span>
        </div>
        <el-button text @click="ui.toggleSidebar" class="collapse-btn">
          <el-icon><Fold v-if="!ui.sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>

      <el-menu
        :default-active="active"
        :collapse="ui.sidebarCollapsed"
        @select="onSelect"
        class="menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item :index="treeHref" :disabled="!groups.currentId">
          <el-icon><Files /></el-icon>
          <template #title>项目树</template>
        </el-menu-item>
        <el-menu-item :index="timelineHref" :disabled="!groups.currentId">
          <el-icon><Calendar /></el-icon>
          <template #title>时间轴</template>
        </el-menu-item>
        <el-menu-item :index="filesHref" :disabled="!groups.currentId">
          <el-icon><FolderOpened /></el-icon>
          <template #title>文件</template>
        </el-menu-item>
        <el-menu-item :index="discussionHref" :disabled="!groups.currentId">
          <el-icon><ChatLineRound /></el-icon>
          <template #title>讨论</template>
        </el-menu-item>
        <el-menu-item index="/inspiration">
          <el-icon><Star /></el-icon>
          <template #title>灵感广场</template>
        </el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <template #title>
            消息 <el-badge v-if="notify.unread" :value="notify.unread" class="msg-badge" />
          </template>
        </el-menu-item>
        <el-menu-item index="/groups">
          <el-icon><UserFilled /></el-icon>
          <template #title>我的小组</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <el-select
            v-if="groups.list.length"
            :model-value="groups.currentId"
            @change="onSwitchGroup"
            placeholder="选择小组"
            size="default"
            style="min-width: 240px"
          >
            <el-option
              v-for="g in groups.list"
              :key="g.id"
              :value="g.id"
              :label="`[${g.course_name}] ${g.name}`"
            >
              <div class="group-opt">
                <span>{{ g.course_name }} · {{ g.name }}</span>
                <el-tag size="small" :type="g.role === 'leader' ? 'warning' : 'info'">
                  {{ g.role === 'leader' ? '组长' : '组员' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <el-button v-else type="primary" plain @click="router.push('/groups')">
            <el-icon><Plus /></el-icon>&nbsp;创建/加入小组
          </el-button>
        </div>

        <div class="topbar-right">
          <el-button text @click="router.push('/notifications')">
            <el-badge :value="notify.unread || ''" :hidden="!notify.unread" :max="99">
              <el-icon size="20"><Bell /></el-icon>
            </el-badge>
          </el-button>
          <ThemeToggle />
          <el-dropdown @command="onUserCmd">
            <div class="user">
              <el-avatar :src="auth.user?.avatar_url" :size="32">{{ initials }}</el-avatar>
              <span class="name">{{ auth.user?.name || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon> 我的资料
                </el-dropdown-item>
                <el-dropdown-item command="groups">
                  <el-icon><UserFilled /></el-icon> 我的小组
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled, Files, Calendar, FolderOpened, ChatLineRound, Star, Bell,
  UserFilled, Plus, ArrowDown, User, SwitchButton, Fold, Expand,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import { useNotifyStore } from '@/stores/notifications'
import { useUIStore } from '@/stores/ui'
import { useWS } from '@/composables/useWS'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const groups = useGroupsStore()
const notify = useNotifyStore()
const ui = useUIStore()
const ws = useWS()

const initials = computed(() =>
  (auth.user?.name || '').slice(0, 1) || 'C',
)
const active = computed(() => {
  const m = route.path.match(/^\/groups\/(\d+)\/(\w+)/)
  if (m) return `/groups/${m[1]}/${m[2]}`
  if (route.path.startsWith('/inspiration')) return '/inspiration'
  return route.path
})
const treeHref = computed(() => `/groups/${groups.currentId}/tree`)
const timelineHref = computed(() => `/groups/${groups.currentId}/timeline`)
const filesHref = computed(() => `/groups/${groups.currentId}/files`)
const discussionHref = computed(() => `/groups/${groups.currentId}/discussion`)

function onSelect(idx: string) {
  if (idx) router.push(idx)
}
function onSwitchGroup(gid: number) {
  groups.setCurrent(gid)
  const m = route.path.match(/^\/groups\/(\d+)\/(\w+)/)
  if (m) router.push(`/groups/${gid}/${m[2]}`)
  else router.push(`/groups/${gid}/tree`)
}
async function onUserCmd(cmd: string) {
  if (cmd === 'logout') {
    auth.clear()
    ws.disconnect()
    router.push('/login')
  } else if (cmd === 'profile') router.push('/profile')
  else if (cmd === 'groups') router.push('/groups')
}

onMounted(async () => {
  try {
    if (auth.isAuthed && !auth.user) await auth.fetchMe()
    await groups.refresh()
    void notify.refresh()
    ws.connect()
    ws.on('notification.new', (data) => {
      notify.push({
        id: Date.now(),
        type: (data as any).type,
        payload: (data as any).payload,
        created_at: new Date().toISOString(),
      } as any)
    })
  } catch {}
})

// route → currentId sync
watch(() => route.params.gid, (gid) => {
  if (gid) groups.setCurrent(Number(gid))
})
</script>

<style lang="scss" scoped>
.app-shell { display: flex; height: 100vh; overflow: hidden; }

.sidebar {
  width: 220px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  transition: width .2s ease;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  &.collapsed { width: 64px; }
}

.logo-row {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-color);
}
.logo { display: flex; align-items: center; gap: 4px; font-weight: 700; }
.logo-mark {
  background: var(--color-primary);
  color: #fff;
  width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 8px;
}
.logo-text { color: var(--color-primary); }
.collapse-btn { padding: 4px; }

.menu { border-right: none; flex: 1; overflow-y: auto; }
.menu :deep(.el-menu) { border-right: none; background: transparent; }
.menu :deep(.el-menu-item.is-active) { background: rgba(61,126,255,.08); color: var(--color-primary); }
.msg-badge { margin-left: 8px; }

.main { flex: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; }

.topbar {
  height: 56px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  gap: 12px;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.topbar-right { display: flex; align-items: center; gap: 12px; }

.user {
  display: flex; align-items: center; gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  &:hover { background: var(--bg-soft); }
  .name { font-size: 14px; color: var(--text-primary); }
}
.group-opt { display: flex; align-items: center; justify-content: space-between; gap: 12px; }

.content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}
</style>
