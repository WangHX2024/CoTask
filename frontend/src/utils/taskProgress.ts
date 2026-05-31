/** Bar width / gradient percent; 100% width is only for done/blocked cards. */
export function taskBarPercent(node: { status: string; progress?: number | null }): number {
  const raw = Math.max(0, Math.min(100, Math.round(node.progress || 0)))
  if (node.status === 'done' || node.status === 'blocked') {
    return 100
  }
  if (node.status === 'in_progress') {
    if (raw >= 100) return 30
    return raw
  }
  return raw
}
