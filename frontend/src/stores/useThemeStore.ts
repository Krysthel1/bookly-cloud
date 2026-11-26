import { create } from 'zustand'

interface ThemeState {
  theme: 'light' | 'dark'
  toggleTheme: () => void
  initTheme: () => void
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: 'light',
  initTheme: () => {
    const stored = localStorage.getItem('bookly-theme')
    const preferred = stored === 'dark' ? 'dark' : 'light'
    document.documentElement.classList.toggle('dark', preferred === 'dark')
    set({ theme: preferred })
  },
  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('bookly-theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
    set({ theme: next })
  },
}))
