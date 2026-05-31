import { defineStore } from 'pinia'
import { Api, type GroupBrief } from '@/api'

export const useGroupsStore = defineStore('groups', {
  state: () => ({
    list: [] as GroupBrief[],
    currentId: 0,
    loaded: false,
  }),
  getters: {
    current: (s) => s.list.find((g) => g.id === s.currentId) || null,
    currentRole: (s) =>
      (s.list.find((g) => g.id === s.currentId)?.role) || null,
  },
  actions: {
    /** Keep currentId valid against list; clear when user has no groups. */
    syncCurrentFromList() {
      if (!this.list.length) {
        this.currentId = 0
        return
      }
      if (!this.currentId || !this.list.some((g) => g.id === this.currentId)) {
        this.currentId = this.list[0].id
      }
    },
    hasGroup(id: number) {
      return this.list.some((g) => g.id === id)
    },
    reset() {
      this.list = []
      this.currentId = 0
      this.loaded = false
    },
    async refresh() {
      const list = await Api.listGroups()
      this.list = list
      this.loaded = true
      this.syncCurrentFromList()
    },
    setCurrent(id: number) {
      if (id && this.list.length && !this.hasGroup(id)) return
      this.currentId = id
    },
    async create(payload: { course_name: string; name: string; description?: string }) {
      const g = await Api.createGroup(payload)
      await this.refresh()
      this.currentId = g.id
      return g
    },
    async join(code: string) {
      const g = await Api.joinGroup(code)
      await this.refresh()
      this.currentId = g.id
      return g
    },
  },
  persist: { key: 'cotask-groups', storage: localStorage, pick: ['currentId'] } as any,
})
