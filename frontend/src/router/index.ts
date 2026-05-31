import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGroupsStore } from '@/stores/groups'

const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('@/components/layout/AppShell.vue'),
    meta: { auth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'groups', component: () => import('@/views/Groups.vue') },
      { path: 'groups/:gid(\\d+)/tree', component: () => import('@/views/ProjectTree.vue') },
      { path: 'groups/:gid(\\d+)/timeline', component: () => import('@/views/Timeline.vue') },
      { path: 'groups/:gid(\\d+)/files', component: () => import('@/views/Files.vue') },
      { path: 'groups/:gid(\\d+)/discussion', component: () => import('@/views/Discussion.vue') },
      { path: 'groups/:gid(\\d+)/members', component: () => import('@/views/Members.vue') },
      { path: 'inspiration', component: () => import('@/views/Inspiration.vue') },
      { path: 'inspiration/new', component: () => import('@/views/InspirationEdit.vue') },
      { path: 'inspiration/p/:id(\\d+)', component: () => import('@/views/InspirationDetail.vue') },
      { path: 'inspiration/p/:id(\\d+)/edit', component: () => import('@/views/InspirationEdit.vue') },
      { path: 'notifications', component: () => import('@/views/Notifications.vue') },
      { path: 'profile', component: () => import('@/views/Profile.vue') },
    ],
  },
  { path: '/:catchAll(.*)', redirect: '/dashboard' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

const GROUP_ROUTE_RE = /^\/groups\/(\d+)\/(tree|timeline|files|discussion|members)$/

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isAuthed) return { path: '/login', query: { next: to.fullPath } }
  if (to.meta.guest && auth.isAuthed) return { path: '/dashboard' }

  const m = to.path.match(GROUP_ROUTE_RE)
  if (!m || !auth.isAuthed) return

  const groups = useGroupsStore()
  if (!groups.loaded) {
    try {
      await groups.refresh()
    } catch {
      return { path: '/groups' }
    }
  }

  const gid = Number(m[1])
  const section = m[2]

  if (!groups.list.length) {
    return { path: '/groups' }
  }

  if (!groups.hasGroup(gid)) {
    groups.syncCurrentFromList()
    return { path: `/groups/${groups.currentId}/${section}`, replace: true }
  }

  groups.setCurrent(gid)
})
