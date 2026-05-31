<script setup lang="ts">
const width = defineModel<number>({ required: true })

const props = withDefaults(
  defineProps<{
    min?: number
    max?: number
    storageKey?: string
  }>(),
  {
    min: 160,
    max: 480,
  },
)

function loadStored(): number | null {
  if (!props.storageKey) return null
  try {
    const n = Number(localStorage.getItem(props.storageKey))
    return Number.isFinite(n) ? n : null
  } catch {
    return null
  }
}

function clamp(w: number) {
  return Math.min(props.max, Math.max(props.min, w))
}

const stored = loadStored()
if (stored != null) {
  width.value = clamp(stored)
}

function persist() {
  if (!props.storageKey) return
  try {
    localStorage.setItem(props.storageKey, String(width.value))
  } catch {
    /* ignore */
  }
}

function onPointerDown(e: PointerEvent) {
  if (e.button !== 0) return

  const el = e.currentTarget as HTMLElement
  e.preventDefault()
  e.stopPropagation()

  const startX = e.clientX
  const startW = width.value

  document.body.classList.add('is-col-resizing')
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  try {
    el.setPointerCapture(e.pointerId)
  } catch {
    /* ignore */
  }

  const onMove = (ev: PointerEvent) => {
    width.value = clamp(startW + (ev.clientX - startX))
  }

  const end = (ev: PointerEvent) => {
    try {
      el.releasePointerCapture(ev.pointerId)
    } catch {
      /* ignore */
    }
    el.removeEventListener('pointermove', onMove)
    el.removeEventListener('pointerup', end)
    el.removeEventListener('pointercancel', end)
    document.body.classList.remove('is-col-resizing')
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    persist()
  }

  el.addEventListener('pointermove', onMove)
  el.addEventListener('pointerup', end)
  el.addEventListener('pointercancel', end)
}
</script>

<template>
  <div
    class="resize-handle"
    role="separator"
    aria-orientation="vertical"
    aria-label="拖拽调节宽度"
    tabindex="0"
    @pointerdown="onPointerDown"
  />
</template>

<style scoped lang="scss">
.resize-handle {
  flex: 0 0 14px;
  width: 14px;
  align-self: stretch;
  cursor: col-resize;
  position: relative;
  z-index: 10;
  touch-action: none;
  flex-shrink: 0;
  background: transparent;

  &::after {
    content: '';
    position: absolute;
    left: 50%;
    top: 12px;
    bottom: 12px;
    width: 2px;
    transform: translateX(-50%);
    border-radius: 1px;
    background: var(--border-color);
    transition: background 0.15s ease, width 0.15s ease;
    pointer-events: none;
  }

  &:hover::after,
  &:active::after {
    width: 3px;
    background: var(--color-primary);
  }
}
</style>
