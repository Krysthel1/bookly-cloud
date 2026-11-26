import { create } from 'zustand'
import type { Session } from '@supabase/supabase-js'
import type { UserProfile } from '@/types'
import { supabase } from '@/lib/supabase'
import { apiClient } from '@/lib/api'

interface AuthState {
  session: Session | null
  profile: UserProfile | null
  isLoading: boolean
  isInitialized: boolean
  setSession: (session: Session | null) => void
  fetchProfile: () => Promise<UserProfile | null>
  initialize: () => Promise<void>
  signOut: () => Promise<void>
  isAdmin: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  profile: null,
  isLoading: false,
  isInitialized: false,

  setSession: (session) => set({ session }),

  fetchProfile: async () => {
    const session = get().session
    if (!session) {
      set({ profile: null })
      return null
    }
    try {
      const { data } = await apiClient.get<UserProfile>('/auth/me')
      set({ profile: data })
      return data
    } catch {
      set({ profile: null })
      return null
    }
  },

  initialize: async () => {
    if (get().isInitialized) return
    set({ isLoading: true })
    try {
      const { data } = await supabase.auth.getSession()
      set({ session: data.session })
      if (data.session) {
        await get().fetchProfile()
      }
      supabase.auth.onAuthStateChange(async (_event, newSession) => {
        set({ session: newSession })
        if (newSession) {
          await get().fetchProfile()
        } else {
          set({ profile: null })
        }
      })
    } finally {
      set({ isLoading: false, isInitialized: true })
    }
  },

  signOut: async () => {
    await supabase.auth.signOut()
    set({ session: null, profile: null })
  },

  isAdmin: () => {
    const roles = get().profile?.roles || []
    return roles.includes('admin')
  },
}))
