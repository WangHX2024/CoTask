<template>
  <div class="tree-canvas">
    <template v-if="rootNodes.length">
      <TreeBranch
        v-for="n in rootNodes"
        :key="n.id"
        :node="n"
        :depth="0"
        :members="members"
        :node-map="visibleMap"
        :children-map="visibleChildrenMap"
        :selected-id="selectedId"
        :current-role="currentRole"
        :expanded="expanded"
        @toggle="onToggle"
        @select="onSelect"
        @add-child="onAddChild"
        @delete="onDelete"
        @drop-on="onDropOn"
      />
    </template>
    <el-empty v-else description="还没有任务节点，点击 + 节点 开始拆分项目" :image-size="120" />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import type { TaskNode, MemberInfo } from '@/api'
import TreeBranch from './TreeBranch.vue'

const props = defineProps<{
  nodes: TaskNode[]
  focusOnMine: boolean
  currentUserId: number
  currentRole: 'leader' | 'member' | null
  selectedId: number
  members: MemberInfo[]
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'add-child', parentId: number): void
  (e: 'delete', id: number): void
  (e: 'drop', payload: { id: number; newParentId: number | null; position: number }): void
}>()

// expand-by-default
const expanded = reactive<Record<number, boolean>>({})

function onToggle(id: number) {
  expanded[id] = !(expanded[id] !== false)
}
function onSelect(id: number) {
  emit('select', id)
}
function onAddChild(id: number) {
  emit('add-child', id)
}
function onDelete(id: number) {
  emit('delete', id)
}
function onDropOn(payload: { id: number; newParentId: number | null; position: number }) {
  emit('drop', payload)
}

// build child index for quick subtree lookups
const childIndex = computed(() => {
  const m = new Map<number | null, TaskNode[]>()
  for (const n of props.nodes) {
    const pid = n.parent_id ?? null
    if (!m.has(pid)) m.set(pid, [])
    m.get(pid)!.push(n)
  }
  for (const arr of m.values()) arr.sort((a, b) => a.position - b.position)
  return m
})

// determine which nodes are visible in focus-on-mine mode: keep a node if itself
// or any descendant has currentUserId as assignee. Always include ancestors of visible nodes.
const visibleSet = computed<Set<number>>(() => {
  if (!props.focusOnMine) return new Set(props.nodes.map((n) => n.id))
  const out = new Set<number>()
  const byId = new Map<number, TaskNode>()
  for (const n of props.nodes) byId.set(n.id, n)
  // collect direct hits
  const hits: TaskNode[] = []
  for (const n of props.nodes) {
    if ((n.assignees || []).includes(props.currentUserId)) hits.push(n)
  }
  // include subtree of each hit
  function pushSubtree(root: TaskNode) {
    out.add(root.id)
    const kids = childIndex.value.get(root.id) || []
    for (const c of kids) pushSubtree(c)
  }
  for (const h of hits) pushSubtree(h)
  // include ancestors
  for (const id of Array.from(out)) {
    let cur = byId.get(id) || null
    while (cur && cur.parent_id != null) {
      out.add(cur.parent_id)
      cur = byId.get(cur.parent_id) || null
    }
  }
  return out
})

const visibleMap = computed(() => {
  const m = new Map<number, TaskNode>()
  for (const n of props.nodes) if (visibleSet.value.has(n.id)) m.set(n.id, n)
  return m
})

const visibleChildrenMap = computed(() => {
  const m = new Map<number | null, TaskNode[]>()
  for (const n of props.nodes) {
    if (!visibleSet.value.has(n.id)) continue
    const pid = n.parent_id ?? null
    if (!m.has(pid)) m.set(pid, [])
    m.get(pid)!.push(n)
  }
  for (const arr of m.values()) arr.sort((a, b) => a.position - b.position)
  return m
})

const rootNodes = computed(() => visibleChildrenMap.value.get(null) || [])
</script>

<style lang="scss" scoped>
.tree-canvas {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px;
}
</style>
