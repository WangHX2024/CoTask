import { defineStore } from 'pinia'
import { Api, type NotificationItem } from '@/api'

export const useNotifyStore = defineStore('notify', {
  state: () => ({
    items: [] as NotificationItem[],
    unread: 0,
  }),
  actions: {
    async refresh() {
      this.items = await Api.notifications({ limit: 50 })
      this.unread = this.items.filter((i) => !i.read_at).length
    },
    async refreshCount() {
      const r = await Api.unreadCount()
      this.unread = r.count
    },
    async markRead(ids?: number[]) {
      await Api.markRead(ids)
      await this.refresh()
    },
    async clearAll() {
      await Api.clearNotifications()
      this.items = []
      this.unread = 0
    },
    push(item: NotificationItem) {
      this.items.unshift(item)
      this.unread += 1
    },
  },
})
