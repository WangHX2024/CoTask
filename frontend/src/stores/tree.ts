import { defineStore } from 'pinia'
import { Api, type NodePatchResult, type TaskNode, type TreeResponse } from '@/api'

export const useTreeStore = defineStore('tree', {
  state: () => ({
    groupId: 0,
    version: 0,
    nodes: [] as TaskNode[],
    loading: false,
    selectedId: 0,
    focusOnMine: false,
    /** Debounce WS tree reload to avoid racing local PATCH (assignees, etc.). */
    _wsReloadTimer: null as ReturnType<typeof setTimeout> | null,
    lastPatchedAt: 0,
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
    _patchNodeInStore(node: TaskNode) {
      const idx = this.nodes.findIndex((n) => n.id === node.id)
      if (idx >= 0) {
        this.nodes[idx] = { ...this.nodes[idx], ...node }
      }
    },
    _applyCascade(cascade: TaskNode[] = []) {
      for (const n of cascade) this._patchNodeInStore(n)
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
      await this.load(this.groupId)
      this.selectedId = node.id
      return node
    },
    async updateNode(id: number, patch: any) {
      const updated: NodePatchResult = await Api.updateNode(this.groupId, id, patch)
      this._patchNodeInStore(updated)
      if (updated.cascade?.length) {
        this._applyCascade(updated.cascade)
      }
      const versions = [
        updated.version,
        ...(updated.cascade || []).map((n) => n.version),
      ]
      this.version = Math.max(this.version, ...versions)
      this.lastPatchedAt = Date.now()
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
      if (!this.groupId) return
      // Skip immediate reload right after our own PATCH (WS echo races optimistic version).
      if (Date.now() - this.lastPatchedAt < 1500) return
      if (this._wsReloadTimer) clearTimeout(this._wsReloadTimer)
      this._wsReloadTimer = setTimeout(() => {
        this._wsReloadTimer = null
        void this.load(this.groupId)
      }, 400)
    },
  },
})
