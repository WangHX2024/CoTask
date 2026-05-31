<script setup lang="ts">
import { Files, Calendar } from '@element-plus/icons-vue'
import SegmentedControl, { type SegmentOption } from './SegmentedControl.vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  mode: 'tree' | 'timeline'
  groupId: number
}>()

const router = useRouter()

const options: SegmentOption<'tree' | 'timeline'>[] = [
  { label: '项目树', value: 'tree', icon: Files },
  { label: '时间轴', value: 'timeline', icon: Calendar },
]

function onChange(v: 'tree' | 'timeline') {
  if (v === props.mode) return
  const base = `/groups/${props.groupId}`
  void router.push(v === 'tree' ? `${base}/tree` : `${base}/timeline`)
}
</script>

<template>
  <SegmentedControl
    class="tree-timeline-switcher"
    :model-value="mode"
    :options="options"
    size="sm"
    @change="onChange"
  />
</template>

<style scoped lang="scss">
.tree-timeline-switcher {
  flex-shrink: 0;
}
</style>
