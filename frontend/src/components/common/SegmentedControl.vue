<script setup lang="ts" generic="T extends string | number">
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick, type Component } from 'vue'

export interface SegmentOption<V extends string | number = string> {
  label: string
  value: V
  /** Optional count badge (hidden when undefined or 0) */
  badge?: number | string
  /** Optional leading icon (Element Plus icon component) */
  icon?: Component
}

const props = withDefaults(
  defineProps<{
    modelValue: T
    options: SegmentOption<T>[]
    size?: 'sm' | 'md'
  }>(),
  { size: 'sm' },
)

const emit = defineEmits<{
  'update:modelValue': [value: T]
  change: [value: T]
}>()

const rootRef = ref<HTMLElement | null>(null)
const indicatorReady = ref(false)
const indicatorStyle = ref<Record<string, string>>({})

const activeIndex = computed(() => {
  const i = props.options.findIndex((o) => o.value === props.modelValue)
  return i >= 0 ? i : 0
})

function syncIndicator() {
  const root = rootRef.value
  if (!root) return
  const buttons = root.querySelectorAll<HTMLButtonElement>('.segmented-control__btn')
  const btn = buttons[activeIndex.value]
  if (!btn) return
  indicatorStyle.value = {
    width: `${btn.offsetWidth}px`,
    transform: `translateX(${btn.offsetLeft}px)`,
  }
  indicatorReady.value = true
}

let resizeObserver: ResizeObserver | undefined

onMounted(async () => {
  await nextTick()
  syncIndicator()
  if (rootRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => syncIndicator())
    resizeObserver.observe(rootRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

watch(
  () => [props.modelValue, props.options] as const,
  async () => {
    await nextTick()
    requestAnimationFrame(() => syncIndicator())
  },
)

function select(value: T) {
  if (value !== props.modelValue) {
    emit('update:modelValue', value)
    emit('change', value)
  }
}
</script>

<template>
  <div
    ref="rootRef"
    class="segmented-control"
    :class="[`segmented-control--${size}`, { 'is-ready': indicatorReady }]"
    role="tablist"
  >
    <span
      class="segmented-control__indicator"
      :style="indicatorStyle"
      aria-hidden="true"
    />
    <button
      v-for="opt in options"
      :key="String(opt.value)"
      type="button"
      class="segmented-control__btn"
      :class="{ active: opt.value === modelValue }"
      role="tab"
      :aria-selected="opt.value === modelValue"
      @click="select(opt.value)"
    >
      <el-icon v-if="opt.icon" class="segmented-control__icon" aria-hidden="true">
        <component :is="opt.icon" />
      </el-icon>
      <span class="segmented-control__label">{{ opt.label }}</span>
      <span
        v-if="opt.badge != null && opt.badge !== 0"
        class="segmented-control__badge"
      >{{ opt.badge }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
.segmented-control {
  position: relative;
  display: inline-flex;
  align-items: stretch;
  padding: 3px;
  background: var(--bg-soft);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  gap: 0;
}

.segmented-control__indicator {
  position: absolute;
  top: 3px;
  left: 0;
  height: calc(100% - 6px);
  border-radius: var(--radius-full);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  pointer-events: none;
  opacity: 0;
  transition:
    transform 0.22s cubic-bezier(0.4, 0, 0.2, 1),
    width 0.22s cubic-bezier(0.4, 0, 0.2, 1),
    opacity 0.12s ease;
}

.segmented-control.is-ready .segmented-control__indicator {
  opacity: 1;
}

.segmented-control__btn {
  position: relative;
  z-index: 1;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  /* Keep weight constant so active tab does not resize and jank the indicator */
  font-weight: 600;
  color: var(--text-tertiary);
  white-space: nowrap;
  transition: color 0.15s ease;
  line-height: 1.2;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);

  &:hover:not(.active) {
    color: var(--text-secondary);
  }

  &.active {
    color: var(--color-primary);
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary-light);
    outline-offset: 1px;
    border-radius: var(--radius-full);
  }
}

.segmented-control__icon {
  font-size: 14px;
  flex-shrink: 0;
}

.segmented-control__label {
  line-height: 1.2;
}

.segmented-control--sm .segmented-control__btn {
  padding: 4px 12px;
  font-size: var(--fs-sm);
  min-height: 28px;
  gap: 5px;
}

.segmented-control--md .segmented-control__btn {
  padding: 7px 16px;
  font-size: var(--fs-base);
  min-height: 32px;
}

.segmented-control__badge {
  font-size: var(--fs-xs);
  font-weight: 600;
  line-height: 1.2;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: var(--bg-soft);
  color: var(--text-tertiary);
}

.segmented-control__btn.active .segmented-control__badge {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
</style>
