<script setup lang="ts">
import { computed } from 'vue'
import type { TaskNode } from '@/api'
import TemplatePreviewBranch from './TemplatePreviewBranch.vue'
import { buildPreviewTree } from './templatePreviewTree'

const props = defineProps<{
  nodes: TaskNode[]
}>()

const roots = computed(() => buildPreviewTree(props.nodes))
</script>

<template>
  <ul v-if="roots.length" class="tree-preview">
    <TemplatePreviewBranch
      v-for="(item, idx) in roots"
      :key="item.node.id"
      :item="item"
      :is-last="idx === roots.length - 1"
      :is-root="true"
    />
  </ul>
</template>

<style scoped lang="scss">
.tree-preview {
  /* trunk-x = horizontal center of track column (guide / 2) */
  --tree-row-h: 30px;
  --tree-guide: 20px;
  --tree-trunk-x: calc(var(--tree-guide) / 2);
  --tree-dot-size: 8px;
  --tree-leaf-dot-size: 6px;

  list-style: none;
  margin: 0;
  padding: 0;
}
</style>
