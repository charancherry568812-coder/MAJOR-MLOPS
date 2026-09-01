/** Zustand auth store for managing user state. */
import { create } from 'zustand'

export interface User {
  id: string; email: string; full_name: string
  role: { id: string; name: string; description: string }
  is_active: boolean
}

interface AuthState {
  user: User | null; isAuthenticated: boolean
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void; setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: (() => { try { const u = localStorage.getItem('user'); return u ? JSON.parse(u) : null } catch { return null } })(),
  isAuthenticated: !!localStorage.getItem('access_token'),
  login: (user, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    set({ user: null, isAuthenticated: false })
  },
  setUser: (user) => { localStorage.setItem('user', JSON.stringify(user)); set({ user }) },
}))
