import type { TaskNode } from '@/api'

export interface PreviewTreeNode {
  node: TaskNode
  children: PreviewTreeNode[]
}

/** Build an ordered tree from flat task nodes (supports multi-level branches and leaves). */
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

export function previewTreeStats(nodes: TaskNode[]): string {
  if (!nodes.length) return ''
  const leaves = nodes.filter((n) => n.is_leaf).length
  const maxDepth = Math.max(...nodes.map((n) => n.depth))
  return `${nodes.length} 个节点 · ${leaves} 个叶子 · ${maxDepth + 1} 层`
}
