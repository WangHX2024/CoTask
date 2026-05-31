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
        <el-menu-item :index="treeHref" :disabled="!effectiveGroupId">
          <el-icon><Files /></el-icon>
          <template #title>项目树</template>
        </el-menu-item>
        <el-menu-item :index="timelineHref" :disabled="!effectiveGroupId">
          <el-icon><Calendar /></el-icon>
          <template #title>时间轴</template>
        </el-menu-item>
        <el-menu-item :index="filesHref" :disabled="!effectiveGroupId">
          <el-icon><FolderOpened /></el-icon>
          <template #title>文件</template>
        </el-menu-item>
        <el-menu-item :index="discussionHref" :disabled="!effectiveGroupId">
          <el-icon><ChatLineRound /></el-icon>
          <template #title>讨论</template>
        </el-menu-item>
        <el-menu-item index="/inspiration">
          <el-icon><Star /></el-icon>
          <template #title>灵感广场</template>
        </el-menu-item>
        <el-menu-item index="/notifications" class="menu-item--notify">
          <el-icon><Bell /></el-icon>
          <template #title>
            <span class="menu-item-title">
              <span>消息</span>
              <el-badge
                v-if="notify.unread"
                :value="notify.unread"
                :max="99"
                class="msg-badge"
              />
            </span>
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
          <GroupSelect
            v-if="groups.list.length"
            :groups="groups.list"
            :model-value="groups.currentId"
            @update:model-value="onSwitchGroup"
          />
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

    <OnboardingWizard
      v-model="showOnboarding"
      :initial-prefs="onboardingPrefs"
      @completed="onOnboardingDone"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
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
import GroupSelect from '@/components/common/GroupSelect.vue'
import OnboardingWizard from '@/components/onboarding/OnboardingWizard.vue'
import { Api } from '@/api'
import { isOnboardingCompleted } from '@/utils/onboarding'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const groups = useGroupsStore()
const notify = useNotifyStore()
const ui = useUIStore()
const ws = useWS()

const showOnboarding = ref(false)
const onboardingPrefs = ref<Record<string, unknown> | null>(null)

const initials = computed(() =>
  (auth.user?.name || '').slice(0, 1) || 'C',
)
const active = computed(() => {
  const m = route.path.match(/^\/groups\/(\d+)\/(\w+)/)
  if (m) return `/groups/${m[1]}/${m[2]}`
  if (route.path.startsWith('/inspiration')) return '/inspiration'
  return route.path
})
/** Valid group id for nav links; 0 when user has no groups. */
const effectiveGroupId = computed(() => {
  if (!groups.list.length) return 0
  if (groups.currentId && groups.list.some((g) => g.id === groups.currentId)) {
    return groups.currentId
  }
  return groups.list[0].id
})

const treeHref = computed(() => `/groups/${effectiveGroupId.value}/tree`)
const timelineHref = computed(() => `/groups/${effectiveGroupId.value}/timeline`)
const filesHref = computed(() => `/groups/${effectiveGroupId.value}/files`)
const discussionHref = computed(() => `/groups/${effectiveGroupId.value}/discussion`)

function onSelect(idx: string) {
  if (idx) router.push(idx)
}
function onSwitchGroup(gid: number | null) {
  if (gid == null) return
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

async function maybeOpenOnboarding() {
  try {
    const me = await Api.me()
    onboardingPrefs.value = (me.prefs as Record<string, unknown>) || {}
    if (!isOnboardingCompleted(onboardingPrefs.value)) {
      showOnboarding.value = true
    }
  } catch {
    // ignore — user can complete onboarding from profile later
  }
}

function onOnboardingDone() {
  onboardingPrefs.value = {
    ...(onboardingPrefs.value || {}),
    onboarding: { completed: true },
  }
}

onMounted(async () => {
  try {
    if (auth.isAuthed && !auth.user) await auth.fetchMe()
    await groups.refresh()
    void notify.refresh()
    void maybeOpenOnboarding()
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

// route → currentId sync (only for groups the user belongs to)
watch(() => route.params.gid, (gid) => {
  if (!gid) return
  const n = Number(gid)
  if (groups.hasGroup(n)) groups.setCurrent(n)
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

/* Unread count beside menu title (inline pill, not floating on icon) */
.menu :deep(.menu-item--notify) {
  .menu-item-title {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    line-height: 1;
    vertical-align: middle;
  }

  .msg-badge {
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
    line-height: 1;
    vertical-align: middle;

    .el-badge__content {
      position: static;
      transform: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
  }
}

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

/* ---------- Content area ---------- */
.content {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
}
</style>
