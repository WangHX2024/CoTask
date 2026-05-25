<template>
  <div class="tb">
    <div
      class="tb-row"
      :draggable="canDrag"
      @dragstart="onDragStart"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent.stop="onDrop"
      :class="{ 'drag-over': dragOver }"
    >
      <span class="caret" @click.stop="toggle">
        <el-icon v-if="hasChildren" :class="{ rot: isOpen }"><CaretRight /></el-icon>
        <span v-else class="caret-dot" />
      </span>

      <TaskNodeCard
        :node="node"
        :members="members"
        :selected="selectedId === node.id"
        :can-edit="canEdit"
        class="tb-card"
        @click="emit('select', node.id)"
        @add-child="emit('add-child', node.id)"
        @delete="emit('delete', node.id)"
      />
    </div>

    <transition name="branch">
      <div
        v-if="hasChildren && isOpen"
        class="tb-children"
        :style="{ marginLeft: `${24}px` }"
      >
        <TreeBranch
          v-for="c in children"
          :key="c.id"
          :node="c"
          :depth="depth + 1"
          :members="members"
          :node-map="nodeMap"
          :children-map="childrenMap"
          :selected-id="selectedId"
          :current-role="currentRole"
          :expanded="expanded"
          @toggle="(id: number) => emit('toggle', id)"
          @select="(id: number) => emit('select', id)"
          @add-child="(id: number) => emit('add-child', id)"
          @delete="(id: number) => emit('delete', id)"
          @drop-on="(p: any) => emit('drop-on', p)"
        />

        <div v-if="canEdit && !node.is_leaf" class="add-child-row">
          <el-button
            size="small"
            text
            type="primary"
            @click="emit('add-child', node.id)"
          >
            <el-icon><Plus /></el-icon>&nbsp;子任务
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { CaretRight, Plus } from '@element-plus/icons-vue'
import type { TaskNode, MemberInfo } from '@/api'
import TaskNodeCard from './TaskNodeCard.vue'

const props = defineProps<{
  node: TaskNode
  depth: number
  members: MemberInfo[]
  nodeMap: Map<number, TaskNode>
  childrenMap: Map<number | null, TaskNode[]>
  selectedId: number
  currentRole: 'leader' | 'member' | null
  expanded: Record<number, boolean>
}>()

const emit = defineEmits<{
  (e: 'toggle', id: number): void
  (e: 'select', id: number): void
  (e: 'add-child', parentId: number): void
  (e: 'delete', id: number): void
  (e: 'drop-on', payload: { id: number; newParentId: number | null; position: number }): void
}>()

const canEdit = computed(() => props.currentRole === 'leader')
const canDrag = computed(() => canEdit.value)

const children = computed(() => props.childrenMap.get(props.node.id) || [])
const hasChildren = computed(() => children.value.length > 0)

// expanded by default: undefined → true; only false collapses
const isOpen = computed(() => props.expanded[props.node.id] !== false)

function toggle() {
  if (!hasChildren.value) return
  emit('toggle', props.node.id)
}

const dragOver = ref(false)

function onDragStart(ev: DragEvent) {
  if (!canDrag.value) {
    ev.preventDefault()
    return
  }
  ev.dataTransfer?.setData('text/plain', String(props.node.id))
  if (ev.dataTransfer) ev.dataTransfer.effectAllowed = 'move'
}
function onDragOver(ev: DragEvent) {
  if (!canEdit.value) return
  if (ev.dataTransfer) ev.dataTransfer.dropEffect = 'move'
  dragOver.value = true
}
function onDragLeave() {
  dragOver.value = false
}
function onDrop(ev: DragEvent) {
  dragOver.value = false
  if (!canEdit.value) return
  const sid = Number(ev.dataTransfer?.getData('text/plain') || 0)
  if (!sid || sid === props.node.id) return
  const dragged = props.nodeMap.get(sid)
  if (!dragged) return
  // disallow dropping onto a descendant
  if (props.node.path?.startsWith(dragged.path || '__none__')) return
  // reorder within the same parent: place dragged before this node
  if (dragged.parent_id === props.node.parent_id) {
    const siblings = props.childrenMap.get(props.node.parent_id) || []
    const targetIdx = siblings.findIndex((s) => s.id === props.node.id)
    emit('drop-on', {
      id: dragged.id,
      newParentId: props.node.parent_id,
      position: targetIdx,
    })
  }
}
</script>

<style lang="scss" scoped>
.tb {
  position: relative;
}
.tb-row {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--radius-md);
  padding: 2px;
  &.drag-over {
    background: rgba(61,126,255,0.08);
    outline: 2px dashed var(--color-primary);
    outline-offset: -2px;
  }
}
.caret {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: 4px;
  &:hover { background: var(--bg-soft); }
  .el-icon {
    transition: transform .15s ease;
    font-size: 12px;
  }
  .el-icon.rot { transform: rotate(90deg); }
  .caret-dot {
    width: 4px; height: 4px;
    background: var(--border-color);
    border-radius: 50%;
  }
}
.tb-card { flex: 1; min-width: 0; }

.tb-children {
  position: relative;
  border-left: 1px dashed var(--border-color);
  padding-left: 12px;
  padding-top: 6px;
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.add-child-row {
  padding-left: 24px;
}

.branch-enter-active, .branch-leave-active {
  transition: opacity .2s, transform .2s;
}
.branch-enter-from, .branch-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
