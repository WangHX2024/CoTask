<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: ui.sidebarCollapsed }">
      <div class="logo-row" :class="{ 'logo-row--compact': ui.sidebarCollapsed }">
        <div v-if="ui.sidebarCollapsed" class="logo-slot">
          <div class="sidebar-brand">
            <CoTaskLogo size="sm" variant="on-light" :show-wordmark="false" />
          </div>
          <el-button
            text
            class="collapse-btn collapse-btn--reveal"
            aria-label="展开侧栏"
            @click="ui.toggleSidebar"
          >
            <el-icon :size="16"><Expand /></el-icon>
          </el-button>
        </div>
        <template v-else>
          <div class="sidebar-brand">
            <CoTaskLogo size="sm" variant="on-light" :show-wordmark="true" />
          </div>
          <el-button
            text
            class="collapse-btn"
            aria-label="收起侧栏"
            @click="ui.toggleSidebar"
          >
            <el-icon><Fold /></el-icon>
          </el-button>
        </template>
      </div>

      <el-menu
        :default-active="active"
        :collapse="ui.sidebarCollapsed"
        :collapse-transition="false"
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
          <el-icon><School /></el-icon>
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
            class="group-select"
            popper-class="group-select-popper"
            placeholder="选择小组"
            @change="onSwitchGroup"
          >
            <template #prefix>
              <el-icon class="group-select-icon"><School /></el-icon>
            </template>
            <template v-if="currentGroup" #label>
              <span class="group-select-value">
                <span class="group-select-course">{{ currentGroup.course_name }}</span>
                <span class="group-select-name">{{ currentGroup.name }}</span>
                <span
                  class="group-select-role"
                  :class="currentGroup.role"
                >{{ currentGroup.role === 'leader' ? '组长' : '组员' }}</span>
              </span>
            </template>
            <el-option
              v-for="g in groups.list"
              :key="g.id"
              :value="g.id"
              :label="`${g.course_name} · ${g.name}`"
            >
              <div class="group-opt">
                <span class="group-opt-text">
                  <span class="group-opt-course">{{ g.course_name }}</span>
                  <span class="group-opt-name">{{ g.name }}</span>
                </span>
                <span class="group-opt-role" :class="g.role">
                  {{ g.role === 'leader' ? '组长' : '组员' }}
                </span>
              </div>
            </el-option>
          </el-select>
          <el-button v-else type="primary" plain @click="router.push('/groups')">
            <el-icon><Plus /></el-icon>&nbsp;创建/加入小组
          </el-button>
        </div>

        <div class="topbar-right">
          <el-button
            text
            class="topbar-icon-btn"
            aria-label="消息通知"
            @click="router.push('/notifications')"
          >
            <el-badge
              :value="notify.unread || ''"
              :hidden="!notify.unread"
              :max="99"
              class="topbar-badge"
            >
              <el-icon :size="20"><Bell /></el-icon>
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
                  <el-icon><School /></el-icon> 我的小组
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
  Plus, ArrowDown, User, SwitchButton, Fold, Expand, School,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'
import { useNotifyStore } from '@/stores/notifications'
import { useUIStore } from '@/stores/ui'
import { useWS } from '@/composables/useWS'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import CoTaskLogo from '@/components/common/CoTaskLogo.vue'

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

const currentGroup = computed(() =>
  groups.list.find((g) => g.id === groups.currentId) ?? null,
)

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

/* ---------- Sidebar — lightweight, blends with page ---------- */
.sidebar {
  /* Match Element Plus collapse menu width: icon + horizontal padding × 2 */
  --sidebar-collapsed-width: 64px;
  --sidebar-collapsed-hit: 44px;
  --sidebar-logo-slot: 28px; /* matches CoTaskLogo sm mark */
  width: 224px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-subtle);
  transition: width 200ms ease;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  &.collapsed {
    width: var(--sidebar-collapsed-width);

    /* .menu is on the same node as .el-menu--collapse (the <el-menu> root) */
    .menu.el-menu--collapse {
      --el-menu-base-level-padding: 0px;
      --el-menu-icon-width: 24px;
      width: var(--sidebar-collapsed-hit) !important;
      margin: 0 auto;
      border-right: none;
      /* Match expanded .menu top padding (var(--space-2) on all sides) */
      padding: var(--space-2) 0;

      > :deep(.el-menu-item) {
        width: var(--sidebar-collapsed-hit);
        height: 40px;
        line-height: 40px;
        margin: var(--space-2) 0;
        padding: 0 !important;
        border-radius: var(--radius-sm);
        box-sizing: border-box;
        overflow: hidden;

        .el-menu-tooltip__trigger {
          padding: 0 !important;
          display: inline-flex !important;
          align-items: center !important;
          justify-content: center !important;
        }

        [class^='el-icon'] {
          margin: 0 !important;
          width: auto !important;
        }
      }

      > :deep(.el-menu-item:hover),
      > :deep(.el-menu-item.is-active) {
        background: transparent !important;
      }

      > :deep(.el-menu-item:hover) .el-menu-tooltip__trigger {
        background: var(--bg-soft);
        border-radius: var(--radius-sm);
      }

      > :deep(.el-menu-item.is-active) .el-menu-tooltip__trigger {
        background: var(--color-primary-light);
        border-radius: var(--radius-sm);
      }
    }
  }
}

.logo-row {
  height: 56px;
  min-height: 56px;
  max-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  flex-shrink: 0;
  min-width: 0;
  box-sizing: border-box;
  transition: none;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  min-width: 0;
}

.sidebar.collapsed .logo-row :deep(.cotask-logo) {
  justify-content: center;
}

/* Collapsed: logo only; expand control appears on hover (same 28px slot as mark) */
.logo-row--compact {
  justify-content: center;
  padding: 0;
}

.logo-slot {
  position: relative;
  width: var(--sidebar-logo-slot);
  height: var(--sidebar-logo-slot);
  flex-shrink: 0;

  .sidebar-brand {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.15s ease;

    :deep(.cotask-logo__mark) {
      width: var(--sidebar-logo-slot);
      height: var(--sidebar-logo-slot);
    }
  }

  .collapse-btn--reveal {
    position: absolute;
    inset: 0;
    width: 100% !important;
    height: 100% !important;
    min-height: unset;
    padding: 0 !important;
    margin: 0;
    border-radius: var(--radius-md);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease;
    color: var(--text-secondary);

    &:hover,
    &:focus-visible {
      color: var(--text-primary);
      background: var(--bg-soft) !important;
    }
  }

  &:hover {
    .sidebar-brand {
      opacity: 0;
      pointer-events: none;
    }

    .collapse-btn--reveal {
      opacity: 1;
      pointer-events: auto;
    }
  }
}

.collapse-btn {
  padding: var(--space-1);
  color: var(--text-tertiary);
  flex-shrink: 0;
  &:hover { color: var(--text-primary); }
}

.menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2) var(--space-2);
  background: transparent;

  &:not(.el-menu--collapse) > :deep(.el-menu-item) {
    height: 40px;
    line-height: 40px;
    border-radius: var(--radius-sm);
    margin: var(--space-2) 0;
    padding: 0 var(--space-3) !important;
    color: var(--text-secondary);
    font-size: var(--fs-base);
    transition: background 120ms ease, color 120ms ease;

    &:hover {
      background: var(--bg-soft);
      color: var(--text-primary);
    }

    &.is-active {
      background: var(--color-primary-light) !important;
      color: var(--color-primary) !important;
      font-weight: 500;
    }

    .el-icon {
      font-size: 16px;
      margin-right: var(--space-3);
      color: inherit;
    }
  }

}

.msg-badge { margin-left: var(--space-2); }

/* ---------- Main area ---------- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ---------- Topbar — lighter divider, balanced ---------- */
.topbar {
  height: 56px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  gap: var(--space-3);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;

  :deep(.topbar-icon-btn) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    padding: 0 !important;
    margin: 0;
    vertical-align: middle;

    .el-icon {
      margin: 0;
    }
  }

  :deep(.topbar-icon-trigger) {
    display: inline-flex;
    align-items: center;
  }

  :deep(.topbar-badge) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    vertical-align: middle;
  }
}

.user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: background 120ms ease;

  &:hover { background: var(--bg-soft); }

  .name {
    font-size: var(--fs-base);
    font-weight: 500;
    color: var(--text-primary);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* ---------- Topbar group switcher ---------- */
.group-select {
  width: min(320px, 42vw);

  :deep(.el-select__wrapper) {
    min-height: 36px;
    padding: 0 var(--space-3) 0 var(--space-2);
    background: var(--bg-soft) !important;
    border-radius: var(--control-radius-line) !important;
    box-shadow: none !important;
    transition: background 120ms ease, box-shadow 120ms ease;

    &:hover {
      background: var(--bg-overlay) !important;
      box-shadow: none !important;
    }

    &.is-focused,
    &.is-focus,
    &:focus-within {
      background: var(--bg-card) !important;
      box-shadow: 0 0 0 1px var(--color-primary) inset !important;
    }
  }

  :deep(.el-select__selection) {
    min-width: 0;
  }

  :deep(.el-select__selected-item) {
    overflow: hidden;
  }

  :deep(.el-select__caret) {
    color: var(--text-tertiary);
  }
}

.group-select-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.group-select-value {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  max-width: 100%;
}

.group-select-course {
  flex-shrink: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

.group-select-name {
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-select-role {
  flex-shrink: 0;
  font-size: var(--fs-xs);
  font-weight: 500;
  line-height: 1.4;
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  color: var(--text-tertiary);

  &.leader {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }
}

.group-opt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-1) 0;
}

.group-opt-text {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  min-width: 0;
}

.group-opt-course {
  flex-shrink: 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

.group-opt-name {
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-opt-role {
  flex-shrink: 0;
  font-size: var(--fs-xs);
  font-weight: 500;
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--bg-soft);
  color: var(--text-tertiary);

  &.leader {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }
}

/* ---------- Content area ---------- */
.content {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
}
</style>
