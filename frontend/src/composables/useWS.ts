import { ref } from 'vue'

declare const __VITE_WS_BASE__: string

const WS_BASE = (typeof __VITE_WS_BASE__ === 'string' ? __VITE_WS_BASE__ : '/ws')

type Listener = (data: unknown) => void

const listeners = new Map<string, Set<Listener>>()
let socket: WebSocket | null = null
let connecting = false
let retryTimer: number | null = null
const connected = ref(false)

function fire(event: string, data: unknown) {
  listeners.get(event)?.forEach((cb) => {
    try { cb(data) } catch {}
  })
}

export function useWS() {
  function connect() {
    if (socket || connecting) return
    const token = localStorage.getItem('access_token')
    if (!token) return
    connecting = true
    const url = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}${WS_BASE}?token=${token}`
    try {
      socket = new WebSocket(url)
    } catch (e) {
      connecting = false
      scheduleRetry()
      return
    }
    socket.onopen = () => {
      connected.value = true
      connecting = false
    }
    socket.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        fire(msg.event, msg.data)
      } catch {}
    }
    socket.onclose = () => {
      connected.value = false
      socket = null
      connecting = false
      scheduleRetry()
    }
    socket.onerror = () => {
      try { socket?.close() } catch {}
    }
  }

  function scheduleRetry() {
    if (retryTimer) return
    retryTimer = window.setTimeout(() => {
      retryTimer = null
      connect()
    }, 3000)
  }

  function disconnect() {
    try { socket?.close() } catch {}
    socket = null
  }

  function on(event: string, cb: Listener) {
    if (!listeners.has(event)) listeners.set(event, new Set())
    listeners.get(event)!.add(cb)
    return () => listeners.get(event)!.delete(cb)
  }

  return { connect, disconnect, on, connected }
}
