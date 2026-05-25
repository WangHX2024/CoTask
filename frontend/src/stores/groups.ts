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
    async refresh() {
      const list = await Api.listGroups()
      this.list = list
      this.loaded = true
      if (!this.currentId && list.length) this.currentId = list[0].id
    },
    setCurrent(id: number) {
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
