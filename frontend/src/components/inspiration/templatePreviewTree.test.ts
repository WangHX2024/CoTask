import { describe, expect, it } from 'vitest'
import type { TaskNode } from '@/api'
import { countTerminalNodes, previewTreeStats } from './templatePreviewTree'

function node(id: number, parent_id: number | null, depth: number): TaskNode {
  return {
    id,
    parent_id,
    title: `N${id}`,
    description: '',
    is_leaf: false,
    refined: false,
    status: 'todo',
    progress: 0,
    depth,
    position: 0,
    path: `/${id}/`,
    assignees: [],
    dependencies: [],
    version: 1,
  }
}

describe('previewTreeStats', () => {
  it('uses 末端任务 instead of leaf wording', () => {
    const nodes = [node(1, null, 0), node(2, 1, 1)]
    expect(previewTreeStats(nodes)).toBe('2 个节点 · 1 个末端任务 · 2 层')
    expect(previewTreeStats(nodes)).not.toContain('叶子')
  })

  it('countTerminalNodes ignores is_leaf flag', () => {
    const nodes = [
      { ...node(1, null, 0), is_leaf: true },
      { ...node(2, 1, 1), is_leaf: false },
    ]
    expect(countTerminalNodes(nodes)).toBe(1)
  })
})
