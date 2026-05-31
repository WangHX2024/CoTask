/** Path-aligned tree diff for AI preview (flat old tree vs nested AI result). */
import type { MemberInfo, TaskNode } from '@/api'
import type { AiTreeNode } from '@/utils/aiTreeContext'

export type DiffStatus = 'add' | 'del' | 'edit' | 'same'

export interface TreeNodeSnapshot {
  title: string
  depth: number
  path: string
  start_date: string | null
  end_date: string | null
  assignees: number[]
}

export interface DiffRow {
  title: string
  depth: number
  status: DiffStatus
  path: string
  /** Human-readable meta (dates / assignees) for this column */
  detail?: string
}

function normDate(v: string | null | undefined): string | null {
  if (!v || !String(v).trim()) return null
  return String(v).slice(0, 10)
}

function snapshotFromFlat(n: TaskNode): Omit<TreeNodeSnapshot, 'path' | 'depth'> {
  return {
    title: n.title,
    start_date: normDate(n.start_date),
    end_date: normDate(n.end_date),
    assignees: [...(n.assignees || [])].sort((a, b) => a - b),
  }
}

function snapshotFromNested(n: AiTreeNode | Record<string, unknown>): Omit<TreeNodeSnapshot, 'path' | 'depth'> {
  const raw = n as AiTreeNode
  return {
    title: String(raw.title || ''),
    start_date: normDate(raw.start_date as string | null),
    end_date: normDate(raw.end_date as string | null),
    assignees: [...(raw.assignees || [])].sort((a, b) => a - b),
  }
}

export function buildPathMapFromFlat(nodes: TaskNode[] | undefined): Map<string, TreeNodeSnapshot> {
  const out = new Map<string, TreeNodeSnapshot>()
  if (!nodes?.length) return out

  const byParent = new Map<number | null, TaskNode[]>()
  for (const n of nodes) {
    const pid = n.parent_id ?? null
    if (!byParent.has(pid)) byParent.set(pid, [])
    byParent.get(pid)!.push(n)
  }
  for (const arr of byParent.values()) {
    arr.sort((a, b) => a.position - b.position)
  }

  function walk(parentId: number | null, parentPath: string, depth: number) {
    for (const n of byParent.get(parentId) || []) {
      const path = parentPath ? `${parentPath} / ${n.title}` : n.title
      out.set(path, { ...snapshotFromFlat(n), path, depth })
      walk(n.id, path, depth + 1)
    }
  }
  walk(null, '', 0)
  return out
}

export function buildPathMapFromNested(nodes: AiTreeNode[] | undefined): Map<string, TreeNodeSnapshot> {
  const out = new Map<string, TreeNodeSnapshot>()
  if (!nodes?.length) return out

  function walk(list: AiTreeNode[], parentPath: string, depth: number) {
    for (const n of list) {
      const path = parentPath ? `${parentPath} / ${n.title}` : n.title
      out.set(path, { ...snapshotFromNested(n), path, depth })
      walk(n.children || [], path, depth + 1)
    }
  }
  walk(nodes, '', 0)
  return out
}

function sameAssignees(a: number[], b: number[]) {
  return a.length === b.length && a.every((x, i) => x === b[i])
}

export function hasFieldChanges(old: TreeNodeSnapshot, neu: TreeNodeSnapshot): boolean {
  return (
    old.start_date !== neu.start_date
    || old.end_date !== neu.end_date
    || !sameAssignees(old.assignees, neu.assignees)
  )
}

export function formatAssignees(ids: number[], memberById: Map<number, string>): string {
  if (!ids.length) return '未指定'
  return ids.map((id) => memberById.get(id) || `用户#${id}`).join('、')
}

function formatDateLabel(v: string | null): string {
  return v || '—'
}

/** One-line summary of dates + assignees on a single snapshot */
export function formatSnapshotMeta(
  snap: TreeNodeSnapshot,
  memberById: Map<number, string>,
): string {
  const parts: string[] = []
  if (snap.start_date) parts.push(`开始 ${snap.start_date}`)
  if (snap.end_date) parts.push(`DDL ${snap.end_date}`)
  parts.push(`负责人 ${formatAssignees(snap.assignees, memberById)}`)
  return parts.join(' · ')
}

/** Change line for edit rows (old → new) */
export function formatFieldChanges(
  old: TreeNodeSnapshot,
  neu: TreeNodeSnapshot,
  memberById: Map<number, string>,
): string {
  const parts: string[] = []
  if (old.start_date !== neu.start_date) {
    parts.push(`开始 ${formatDateLabel(old.start_date)}→${formatDateLabel(neu.start_date)}`)
  }
  if (old.end_date !== neu.end_date) {
    parts.push(`DDL ${formatDateLabel(old.end_date)}→${formatDateLabel(neu.end_date)}`)
  }
  if (!sameAssignees(old.assignees, neu.assignees)) {
    parts.push(
      `负责人 ${formatAssignees(old.assignees, memberById)}→${formatAssignees(neu.assignees, memberById)}`,
    )
  }
  return parts.join(' · ')
}

function resolveStatus(
  path: string,
  snap: TreeNodeSnapshot,
  other: Map<string, TreeNodeSnapshot>,
  side: 'old' | 'new',
): DiffStatus {
  const peer = other.get(path)
  if (peer) {
    return hasFieldChanges(snap, peer) || hasFieldChanges(peer, snap) ? 'edit' : 'same'
  }
  const sameTitle = Array.from(other.values()).some((x) => x.title === snap.title)
  return sameTitle ? 'edit' : side === 'old' ? 'del' : 'add'
}

export function memberNameMap(members: MemberInfo[] | undefined): Map<number, string> {
  const m = new Map<number, string>()
  for (const x of members || []) {
    m.set(x.user_id, x.name)
  }
  return m
}

export function buildDiffColumns(
  oldNodes: TaskNode[] | undefined,
  newNodes: AiTreeNode[] | undefined,
  members: MemberInfo[] | undefined,
): { oldRows: DiffRow[]; newRows: DiffRow[] } {
  const oldMap = buildPathMapFromFlat(oldNodes)
  const newMap = buildPathMapFromNested(newNodes)
  const memberById = memberNameMap(members)

  const oldRows: DiffRow[] = []
  for (const snap of oldMap.values()) {
    const status = resolveStatus(snap.path, snap, newMap, 'old')
    const peer = newMap.get(snap.path)
    let detail: string | undefined
    if (status === 'del') {
      detail = formatSnapshotMeta(snap, memberById)
    } else if (status === 'edit' && peer) {
      detail = formatFieldChanges(snap, peer, memberById)
    }
    oldRows.push({ title: snap.title, depth: snap.depth, status, path: snap.path, detail })
  }

  const newRows: DiffRow[] = []
  for (const snap of newMap.values()) {
    const status = resolveStatus(snap.path, snap, oldMap, 'new')
    const peer = oldMap.get(snap.path)
    let detail: string | undefined
    if (status === 'add') {
      detail = formatSnapshotMeta(snap, memberById)
    } else if (status === 'edit' && peer) {
      detail = formatFieldChanges(peer, snap, memberById)
    }
    newRows.push({ title: snap.title, depth: snap.depth, status, path: snap.path, detail })
  }

  return { oldRows, newRows }
}
