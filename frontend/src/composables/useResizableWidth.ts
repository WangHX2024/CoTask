import {
  computed,
  onBeforeUnmount,
  ref,
  watch,
  type Ref,
} from 'vue'

export interface ResizableWidthOptions {
  defaultWidth: number
  /** Sidebar narrowest */
  minWidth: number
  /** Sidebar widest (absolute cap) */
  maxWidth: number
  /** Keep at least this much width for the main (right) column */
  mainMinWidth?: number
  /** Gap + resize handle (px), subtracted with mainMinWidth from split width */
  splitChrome?: number
}

/** Sidebar width for split layouts; pair with ResizeHandle v-model + storageKey. */
export function useResizableWidth(opts: ResizableWidthOptions) {
  const width = ref(opts.defaultWidth)
  const splitWidth = ref(0)
  const mainMin = opts.mainMinWidth ?? 240
  const chrome = opts.splitChrome ?? 46

  let ro: ResizeObserver | null = null

  function bindSplitContainer(el: Ref<HTMLElement | null | undefined>) {
    watch(
      el,
      (node) => {
        ro?.disconnect()
        ro = null
        if (!node) return
        ro = new ResizeObserver((entries) => {
          splitWidth.value = entries[0]?.contentRect.width ?? 0
        })
        ro.observe(node)
        splitWidth.value = node.getBoundingClientRect().width
      },
      { immediate: true },
    )
  }

  onBeforeUnmount(() => {
    ro?.disconnect()
  })

  const effectiveMax = computed(() => {
    if (splitWidth.value > 0) {
      const fromLayout = splitWidth.value - mainMin - chrome
      return Math.max(opts.minWidth, Math.min(opts.maxWidth, Math.floor(fromLayout)))
    }
    return opts.maxWidth
  })

  watch(effectiveMax, (max) => {
    if (width.value > max) width.value = max
  })

  const style = computed(() => ({
    width: `${width.value}px`,
    flexShrink: '0',
  }))

  return {
    width,
    style,
    minWidth: opts.minWidth,
    maxWidth: effectiveMax,
    bindSplitContainer,
  }
}
