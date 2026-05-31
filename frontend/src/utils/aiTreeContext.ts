/** Flat store nodes → nested JSON for AI jobs (tree_gen result / tree_edit context). */
import type { TaskNode } from '@/api'

export interface AiTreeNode {
  title: string
  description: string
  start_date: string | null
  end_date: string | null
  assignees: number[]
  children: AiTreeNode[]
}

function dateForAi(v: string | undefined): string | null {
  return v && v.length ? v : null
}

/** Build nested tree with dates and assignees for AI request/response. */
export function flatNodesToAiTree(nodes: TaskNode[]): AiTreeNode[] {
  const byParent = new Map<number | null, TaskNode[]>()
  for (const n of nodes) {
    const p = n.parent_id
    if (!byParent.has(p)) byParent.set(p, [])
    byParent.get(p)!.push(n)
  }
  for (const arr of byParent.values()) {
    arr.sort((a, b) => a.position - b.position)
  }

  function build(parentId: number | null): AiTreeNode[] {
    return (byParent.get(parentId) || []).map((n) => ({
      title: n.title,
      description: n.description || '',
      start_date: dateForAi(n.start_date),
      end_date: dateForAi(n.end_date),
      assignees: [...(n.assignees || [])],
      children: build(n.id),
    }))
  }

  return build(null)
}

export function aiTreeContextFromFlat(nodes: TaskNode[]): { nodes: AiTreeNode[] } {
  return { nodes: flatNodesToAiTree(nodes) }
}
