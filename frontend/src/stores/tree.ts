import { defineStore } from 'pinia'
import { Api, type TaskNode, type TreeResponse } from '@/api'

export const useTreeStore = defineStore('tree', {
  state: () => ({
    groupId: 0,
    version: 0,
    nodes: [] as TaskNode[],
    loading: false,
    selectedId: 0,
    focusOnMine: false,
  }),
  getters: {
    byId: (s) => {
      const m = new Map<number, TaskNode>()
      for (const n of s.nodes) m.set(n.id, n)
      return m
    },
    childrenOf: (s) => (id: number | null) =>
      s.nodes.filter((n) => n.parent_id === id).sort((a, b) => a.position - b.position),
    selected: (s) => s.nodes.find((n) => n.id === s.selectedId) || null,
    selectedDescendantsCount(): number {
      const id = this.selectedId
      if (!id) return 0
      const path = this.nodes.find((n) => n.id === id)?.path
      if (!path) return 0
      return this.nodes.filter((n) => n.path.startsWith(path) && n.id !== id).length
    },
  },
  actions: {
    apply(resp: TreeResponse) {
      this.groupId = resp.group_id
      this.version = resp.version
      this.nodes = resp.nodes
    },
    async load(gid: number) {
      this.groupId = gid
      this.loading = true
      try {
        this.apply(await Api.getTree(gid))
      } finally {
        this.loading = false
      }
    },
    async createChild(parentId: number | null, payload: any) {
      const node = await Api.createNode(this.groupId, { ...payload, parent_id: parentId })
      // refetch entire tree to keep paths/closure consistent
      await this.load(this.groupId)
      this.selectedId = node.id
      return node
    },
    async updateNode(id: number, patch: any) {
      const updated = await Api.updateNode(this.groupId, id, patch)
      // simple optimistic replace; rely on WS / next load to reconcile depth/path
      const idx = this.nodes.findIndex((n) => n.id === id)
      if (idx >= 0) this.nodes[idx] = { ...this.nodes[idx], ...updated }
      return updated
    },
    async deleteNode(id: number) {
      await Api.deleteNode(this.groupId, id)
      await this.load(this.groupId)
    },
    async moveNode(id: number, newParent: number | null, position?: number) {
      await Api.moveNode(this.groupId, id, newParent, position)
      await this.load(this.groupId)
    },
    setSelected(id: number) {
      this.selectedId = id
    },
    applyWSPatch(_patch: unknown) {
      // for v1.0 we just refetch on tree.updated; finer-grained patches can come later
      if (this.groupId) void this.load(this.groupId)
    },
  },
})
