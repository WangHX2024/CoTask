import { defineStore } from 'pinia'
import { applyTheme, currentTheme, type ThemeMode } from '@/utils/theme'

export const useUIStore = defineStore('ui', {
  state: () => ({
    sidebarCollapsed: false,
    theme: currentTheme(),
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    setTheme(t: ThemeMode) {
      this.theme = t
      applyTheme(t)
    },
  },
  persist: { key: 'cotask-ui', storage: localStorage } as any,
})
