/** Persist AI chat session per group (multi-turn tree_gen / tree_edit). */

export type AiChatScope = 'tree_gen' | 'tree_edit'

export interface AiSession {
  id: number
  scope: AiChatScope
}

function storageKey(groupId: number): string {
  return `cotask-ai-session-${groupId}`
}

export function loadAiSession(groupId: number): AiSession | null {
  try {
    const raw = sessionStorage.getItem(storageKey(groupId))
    if (!raw) return null
    const data = JSON.parse(raw) as AiSession
    const id = typeof data.id === 'number' ? data.id : Number(data.id)
    if (Number.isFinite(id) && (data.scope === 'tree_gen' || data.scope === 'tree_edit')) {
      return { id, scope: data.scope }
    }
  } catch {
    /* ignore */
  }
  return null
}

export function saveAiSession(groupId: number, session: AiSession): void {
  sessionStorage.setItem(storageKey(groupId), JSON.stringify(session))
}

export function clearAiSession(groupId: number): void {
  sessionStorage.removeItem(storageKey(groupId))
}
