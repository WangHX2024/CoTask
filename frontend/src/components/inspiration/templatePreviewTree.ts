import type { TaskNode } from '@/api'

export interface PreviewTreeNode {
  node: TaskNode
  children: PreviewTreeNode[]
}

/** Build an ordered tree from flat task nodes (multi-level branches and terminal nodes). */
export function buildPreviewTree(nodes: TaskNode[]): PreviewTreeNode[] {
  if (!nodes.length) return []

  const items = new Map<number, PreviewTreeNode>()
  for (const n of nodes) {
    items.set(n.id, { node: n, children: [] })
  }

  const roots: PreviewTreeNode[] = []
  for (const n of nodes) {
    const item = items.get(n.id)!
    const pid = n.parent_id
    if (pid != null && items.has(pid)) {
      items.get(pid)!.children.push(item)
    } else {
      roots.push(item)
    }
  }

  const sortNodes = (list: PreviewTreeNode[]) => {
    list.sort((a, b) => a.node.position - b.node.position || a.node.id - b.node.id)
    list.forEach((x) => sortNodes(x.children))
  }
  sortNodes(roots)
  return roots
}

/** Nodes with no children in the tree (by parent_id links, not is_leaf flag). */
export function countTerminalNodes(nodes: TaskNode[]): number {
  if (!nodes.length) return 0
  const parentIds = new Set<number>()
  for (const n of nodes) {
    if (n.parent_id != null) parentIds.add(n.parent_id)
  }
  return nodes.filter((n) => !parentIds.has(n.id)).length
}

export function previewTreeStats(nodes: TaskNode[]): string {
  if (!nodes.length) return ''
  const terminal = countTerminalNodes(nodes)
  const maxDepth = Math.max(...nodes.map((n) => n.depth))
  return `${nodes.length} 个节点 · ${terminal} 个末端任务 · ${maxDepth + 1} 层`
}
