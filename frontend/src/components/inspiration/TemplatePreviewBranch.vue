<script setup lang="ts">
import { computed } from 'vue'
import type { PreviewTreeNode } from './templatePreviewTree'

defineOptions({ name: 'TemplatePreviewBranch' })

const props = defineProps<{
  item: PreviewTreeNode
  isLast?: boolean
  isRoot?: boolean
}>()

const hasChildren = computed(() => props.item.children.length > 0)
</script>

<template>
  <li
    class="tree-preview__node"
    :class="{
      'tree-preview__node--last': isLast,
      'tree-preview__node--root': isRoot,
    }"
  >
    <div
      class="tree-preview__row"
      :class="{
        'tree-preview__row--terminal': !hasChildren,
        'tree-preview__row--branch': hasChildren,
      }"
    >
      <div class="tree-preview__track" aria-hidden="true">
        <span class="tree-preview__dot" />
      </div>
      <span class="tree-preview__title">{{ item.node.title }}</span>
    </div>

    <ul v-if="hasChildren" class="tree-preview__children">
      <TemplatePreviewBranch
        v-for="(child, idx) in item.children"
        :key="child.node.id"
        :item="child"
        :is-last="idx === item.children.length - 1"
        :is-root="false"
      />
    </ul>
  </li>
</template>

<style scoped lang="scss">
.tree-preview__node {
  position: relative;
  list-style: none;
}

.tree-preview__row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: var(--tree-row-h, 30px);
  padding: var(--space-1) 0;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

/* Dot column — center aligns with vertical trunk at guide/2 */
.tree-preview__track {
  position: relative;
  flex-shrink: 0;
  width: var(--tree-guide, 20px);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Horizontal elbow: trunk → dot center in track (non-root only) */
.tree-preview__node:not(.tree-preview__node--root) > .tree-preview__row > .tree-preview__track::before {
  content: '';
  position: absolute;
  left: calc(var(--tree-trunk-x, 10px) - var(--tree-guide, 20px));
  top: 50%;
  width: var(--tree-guide, 20px);
  height: 1px;
  margin-top: -0.5px;
  background: var(--border-color);
}

.tree-preview__row--branch .tree-preview__title {
  font-weight: 600;
  color: var(--text-primary);
}

.tree-preview__row--terminal .tree-preview__title {
  color: var(--text-secondary);
}

.tree-preview__dot {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  width: var(--tree-dot-size, 8px);
  height: var(--tree-dot-size, 8px);
  border-radius: 50%;
  background: var(--color-primary-light);
  border: 1.5px solid var(--color-primary);
  box-sizing: border-box;
}

.tree-preview__row--terminal .tree-preview__dot {
  width: var(--tree-terminal-dot-size, 6px);
  height: var(--tree-terminal-dot-size, 6px);
  border-radius: 1px;
  transform: rotate(45deg);
  background: var(--text-tertiary);
  border: none;
}

.tree-preview__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

/* Vertical trunk: from parent row center through all siblings */
.tree-preview__children {
  position: relative;
  margin: 0 0 0 var(--tree-trunk-x, 10px);
  padding: 0 0 0 calc(var(--tree-guide, 20px) - var(--tree-trunk-x, 10px));
  list-style: none;
}

.tree-preview__children::before {
  content: '';
  position: absolute;
  left: 0;
  top: calc(var(--tree-row-h, 30px) / -2);
  bottom: calc(var(--tree-row-h, 30px) / 2);
  width: 1px;
  margin-left: -0.5px;
  background: var(--border-color);
  pointer-events: none;
}
</style>
