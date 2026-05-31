import { describe, expect, it } from 'vitest'
import type { TaskNode } from '@/api'
import {
  buildDiffColumns,
  buildPathMapFromNested,
  formatFieldChanges,
  hasFieldChanges,
} from './treeDiff'

describe('buildPathMapFromNested', () => {
  it('walks nested children', () => {
    const map = buildPathMapFromNested([
      {
        title: 'Root',
        description: '',
        start_date: null,
        end_date: null,
        assignees: [],
        children: [
          {
            title: 'Child',
            description: '',
            start_date: '2026-05-01',
            end_date: '2026-05-10',
            assignees: [2],
            children: [],
          },
        ],
      },
    ])
    expect(map.has('Root')).toBe(true)
    expect(map.has('Root / Child')).toBe(true)
    expect(map.get('Root / Child')?.end_date).toBe('2026-05-10')
  })
})

describe('buildDiffColumns', () => {
  const members = [{ user_id: 2, name: 'Bob', role: 'member' as const, joined_at: '', contribution: 0, skills: [] }]

  it('marks date and assignee changes as edit with detail', () => {
    const oldNodes: TaskNode[] = [
      {
        id: 1,
        parent_id: null,
        title: 'Task',
        description: '',
        is_leaf: true,
        refined: false,
        start_date: '2026-05-01',
        end_date: '2026-05-10',
        status: 'todo',
        progress: 0,
        depth: 0,
        position: 0,
        path: '/1/',
        assignees: [2],
        dependencies: [],
        version: 1,
      },
    ]
    const { oldRows, newRows } = buildDiffColumns(oldNodes, [
      {
        title: 'Task',
        description: '',
        start_date: '2026-05-02',
        end_date: '2026-05-12',
        assignees: [],
        children: [],
      },
    ], members)
    expect(oldRows[0].status).toBe('edit')
    expect(newRows[0].status).toBe('edit')
    expect(oldRows[0].detail).toContain('开始')
    expect(oldRows[0].detail).toContain('负责人')
    expect(hasFieldChanges(
      { title: 'T', depth: 0, path: 'T', start_date: '2026-05-01', end_date: null, assignees: [1] },
      { title: 'T', depth: 0, path: 'T', start_date: '2026-05-01', end_date: null, assignees: [2] },
    )).toBe(true)
  })

  it('formatFieldChanges shows arrow labels', () => {
    const line = formatFieldChanges(
      { title: 'T', depth: 0, path: 'T', start_date: '2026-05-01', end_date: '2026-05-10', assignees: [2] },
      { title: 'T', depth: 0, path: 'T', start_date: '2026-05-02', end_date: '2026-05-10', assignees: [2] },
      new Map([[2, 'Bob']]),
    )
    expect(line).toMatch(/开始.*→/)
  })
})
