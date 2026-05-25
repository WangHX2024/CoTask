export type ThemeMode = 'light' | 'dark' | 'auto'

const STORAGE_KEY = 'cotask-theme'

export function applyTheme(mode: ThemeMode) {
  const root = document.documentElement
  if (mode === 'auto') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
  } else {
    root.classList.toggle('dark', mode === 'dark')
  }
  localStorage.setItem(STORAGE_KEY, mode)
}

export function currentTheme(): ThemeMode {
  return (localStorage.getItem(STORAGE_KEY) as ThemeMode | null) || 'auto'
}

export function initTheme() {
  applyTheme(currentTheme())
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme() === 'auto') applyTheme('auto')
  })
}
