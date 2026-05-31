import { reactive } from 'vue'

export interface TableColumnDef {
  id: string
  defaultWidth: number
  minWidth: number
  maxWidth?: number
  resizable?: boolean
}

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n))
}

function setResizingCursor(active: boolean) {
  document.body.classList.toggle('is-col-resizing', active)
  document.body.style.cursor = active ? 'col-resize' : ''
  document.body.style.userSelect = active ? 'none' : ''
}

export function useResizableColumns(defs: TableColumnDef[], storageKey?: string) {
  const widths = reactive<Record<string, number>>({})

  function init() {
    let stored: Record<string, number> | null = null
    if (storageKey) {
      try {
        stored = JSON.parse(localStorage.getItem(storageKey) || 'null') as Record<string, number> | null
      } catch {
        stored = null
      }
    }
    for (const d of defs) {
      const raw = stored?.[d.id]
      const max = d.maxWidth ?? 1200
      widths[d.id] = clamp(
        typeof raw === 'number' && Number.isFinite(raw) ? raw : d.defaultWidth,
        d.minWidth,
        max,
      )
    }
  }
  init()

  function persist() {
    if (storageKey) {
      localStorage.setItem(storageKey, JSON.stringify({ ...widths }))
    }
  }

  function isResizable(colId: string) {
    const def = defs.find((d) => d.id === colId)
    return def != null && def.resizable !== false
  }

  function onColumnResize(colId: string, e: PointerEvent) {
    const def = defs.find((d) => d.id === colId)
    if (!def || def.resizable === false) return

    const el = e.currentTarget as HTMLElement | null
    if (!el || e.button !== 0) return

    e.preventDefault()
    e.stopPropagation()

    const startX = e.clientX
    const startW = widths[colId]
    const max = def.maxWidth ?? 1200
    setResizingCursor(true)

    try {
      el.setPointerCapture(e.pointerId)
    } catch {
      /* ignore */
    }

    const onMove = (ev: PointerEvent) => {
      widths[colId] = clamp(startW + (ev.clientX - startX), def.minWidth, max)
    }

    const onUp = (ev: PointerEvent) => {
      setResizingCursor(false)
      try {
        el.releasePointerCapture(ev.pointerId)
      } catch {
        /* ignore */
      }
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerup', onUp)
      el.removeEventListener('pointercancel', onUp)
      persist()
    }

    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerup', onUp)
    el.addEventListener('pointercancel', onUp)
  }

  function colStyle(colId: string) {
    return { width: `${widths[colId]}px` }
  }

  return { widths, isResizable, onColumnResize, colStyle }
}
