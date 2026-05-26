import type { TaskNode } from '@/api'

/** Merge target group tree with template nodes for post-import preview. */
export function buildImportPreviewNodes(
  groupNodes: TaskNode[],
  templateNodes: TaskNode[],
  mode: 'replace' | 'append',
): TaskNode[] {
  if (mode === 'replace') return templateNodes
  if (!groupNodes.length) return templateNodes
  if (!templateNodes.length) return groupNodes
  return [...groupNodes, ...templateNodes]
}

export function importPreviewHint(
  groupNodes: TaskNode[],
  templateNodes: TaskNode[],
  mode: 'replace' | 'append',
): string {
  const gCount = groupNodes.length
  const tCount = templateNodes.length
  if (mode === 'replace') {
    if (!gCount && !tCount) return '导入后小组暂无任务节点'
    if (!gCount) return `将导入 ${tCount} 个节点`
    return `将移除现有 ${gCount} 个节点，替换为模板的 ${tCount} 个节点`
  }
  if (!gCount) return `将在空小组中追加 ${tCount} 个节点`
  if (!tCount) return '模板暂无节点可追加'
  const roots = groupNodes.filter((n) => n.parent_id == null).length
  return `保留现有 ${gCount} 个节点（${roots} 个根），并追加模板 ${tCount} 个节点`
}
