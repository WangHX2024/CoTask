<template>
  <div class="diff-viewer">
    <div class="diff-header">
      <div class="diff-col-head">
        <el-icon><Document /></el-icon>
        <span>当前项目树</span>
        <el-tag size="small" type="info" effect="plain">{{ oldFlat.length }} 节点</el-tag>
      </div>
      <div class="diff-col-head">
        <el-icon><MagicStick /></el-icon>
        <span>AI 建议方案</span>
        <el-tag size="small" type="primary" effect="plain">{{ newFlat.length }} 节点</el-tag>
      </div>
    </div>

    <div class="diff-legend tiny muted">
      <span class="lg-item"><i class="dot dot-add"></i>新增</span>
      <span class="lg-item"><i class="dot dot-edit"></i>变更</span>
      <span class="lg-item"><i class="dot dot-del"></i>删除</span>
      <span class="lg-item"><i class="dot dot-same"></i>未变</span>
    </div>

    <div class="diff-body">
      <div class="diff-col">
        <ul v-if="oldFlat.length" class="diff-list">
          <li
            v-for="(row, i) in oldFlat"
            :key="`o-${i}`"
            class="diff-row"
            :class="`r-${row.status}`"
            :style="{ paddingLeft: `${row.depth * 16 + 12}px` }"
          >
            <span class="diff-marker">{{ markerOld(row.status) }}</span>
            <span class="diff-title">{{ row.title }}</span>
          </li>
        </ul>
        <el-empty v-else description="尚未生成项目树" :image-size="80" />
      </div>
      <div class="diff-col">
        <ul v-if="newFlat.length" class="diff-list">
          <li
            v-for="(row, i) in newFlat"
            :key="`n-${i}`"
            class="diff-row"
            :class="`r-${row.status}`"
            :style="{ paddingLeft: `${row.depth * 16 + 12}px` }"
          >
            <span class="diff-marker">{{ markerNew(row.status) }}</span>
            <span class="diff-title">{{ row.title }}</span>
          </li>
        </ul>
        <el-empty v-else description="AI 未返回结果" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document, MagicStick } from '@element-plus/icons-vue'
import type { TaskNode } from '@/api'

const props = defineProps<{
  oldNodes: TaskNode[] | undefined
  newNodes: any[]
}>()

type DiffStatus = 'add' | 'del' | 'edit' | 'same'
interface DiffRow {
  title: string
  depth: number
  status: DiffStatus
  path: string
}

// build a path-keyed map ("rootTitle/childTitle/...") from a hierarchical node list
function buildPathMap(nodes: any[] | undefined): Map<string, { title: string; depth: number }> {
  const out = new Map<string, { title: string; depth: number }>()
  if (!nodes || !nodes.length) return out

  // group by parent for hierarchical traversal
  const byParent = new Map<number | null, any[]>()
  for (const n of nodes) {
    const pid = n.parent_id ?? null
    if (!byParent.has(pid)) byParent.set(pid, [])
    byParent.get(pid)!.push(n)
  }
  for (const arr of byParent.values()) {
    arr.sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
  }
  function walk(parentId: number | null, parentPath: string, depth: number) {
    const children = byParent.get(parentId) || []
    for (const n of children) {
      const path = parentPath ? `${parentPath} / ${n.title}` : n.title
      out.set(path, { title: n.title, depth })
      walk(n.id, path, depth + 1)
    }
  }
  walk(null, '', 0)
  return out
}

const oldFlat = computed<DiffRow[]>(() => {
  const oldMap = buildPathMap(props.oldNodes)
  const newMap = buildPathMap(props.newNodes)
  const rows: DiffRow[] = []
  for (const [path, v] of oldMap.entries()) {
    let status: DiffStatus = 'same'
    if (!newMap.has(path)) {
      // check if same leaf title exists at different path
      const sameTitle = Array.from(newMap.values()).some((x) => x.title === v.title)
      status = sameTitle ? 'edit' : 'del'
    }
    rows.push({ title: v.title, depth: v.depth, status, path })
  }
  return rows
})

const newFlat = computed<DiffRow[]>(() => {
  const oldMap = buildPathMap(props.oldNodes)
  const newMap = buildPathMap(props.newNodes)
  const rows: DiffRow[] = []
  for (const [path, v] of newMap.entries()) {
    let status: DiffStatus = 'same'
    if (!oldMap.has(path)) {
      const sameTitle = Array.from(oldMap.values()).some((x) => x.title === v.title)
      status = sameTitle ? 'edit' : 'add'
    }
    rows.push({ title: v.title, depth: v.depth, status, path })
  }
  return rows
})

function markerOld(s: DiffStatus) {
  return s === 'del' ? '−' : s === 'edit' ? '~' : '·'
}
function markerNew(s: DiffStatus) {
  return s === 'add' ? '+' : s === 'edit' ? '~' : '·'
}
</script>

<style lang="scss" scoped>
.diff-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
  min-height: 400px;
}
.diff-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.diff-col-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 12px;
  background: var(--bg-soft);
  border-radius: var(--radius-sm);
}
.diff-legend {
  display: flex;
  gap: 14px;
  padding: 0 4px;
  .lg-item { display: inline-flex; align-items: center; gap: 4px; }
  .dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 2px;
  }
  .dot-add  { background: var(--color-success); }
  .dot-edit { background: var(--color-warning); }
  .dot-del  { background: var(--color-danger); }
  .dot-same { background: var(--border-color); }
}
.diff-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}
.diff-col {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  overflow: auto;
  max-height: 480px;
}
.diff-list {
  list-style: none;
  margin: 0;
  padding: 6px 0;
}
.diff-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 13px;
  line-height: 1.4;
  border-left: 3px solid transparent;
  word-break: break-word;

  .diff-marker {
    display: inline-block;
    width: 12px;
    font-weight: 700;
    text-align: center;
    flex-shrink: 0;
  }
  .diff-title { flex: 1; min-width: 0; }

  &.r-add {
    background: rgba(103,194,58,0.08);
    border-left-color: var(--color-success);
    color: #15803D;
    font-weight: 500;
  }
  &.r-del {
    background: rgba(245,108,108,0.06);
    border-left-color: var(--color-danger);
    color: var(--color-danger);
    text-decoration: line-through;
    opacity: 0.85;
  }
  &.r-edit {
    background: rgba(230,162,60,0.08);
    border-left-color: var(--color-warning);
    color: #B45309;
  }
  &.r-same { color: var(--text-secondary); }
}
html.dark {
  .diff-row.r-add  { color: #86EFAC; }
  .diff-row.r-edit { color: #FDE68A; }
  .diff-row.r-del  { color: #FCA5A5; }
}
</style>
