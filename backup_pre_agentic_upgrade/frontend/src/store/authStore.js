/**
 * ScholARA — Auth Store (Zustand)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi, formatApiError } from '@/lib/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /** Validate persisted token against API; clears invalid sessions */
      bootstrapAuth: async () => {
        const persisted = get().token
        const fromLs = localStorage.getItem('scholara_token')
        const token = persisted || fromLs
        if (!token) {
          set({ user: null, token: null, isAuthenticated: false })
          return
        }
        localStorage.setItem('scholara_token', token)
        try {
          const { data } = await authApi.me()
          set({
            token,
            user: { id: data.id, username: data.username, email: data.email },
            isAuthenticated: true,
            error: null,
          })
        } catch {
          localStorage.removeItem('scholara_token')
          localStorage.removeItem('scholara_user')
          set({ user: null, token: null, isAuthenticated: false, error: null })
        }
      },

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const identifier = String(credentials.email || credentials.username || '').trim()
          const { data } = await authApi.login({
            email: identifier,
            password: credentials.password,
          })
          localStorage.setItem('scholara_token', data.access_token)
          set({
            token: data.access_token,
            user: { id: data.user_id, username: data.username, email: data.email },
            isAuthenticated: true,
            isLoading: false,
          })
          return { success: true }
        } catch (err) {
          const msg = formatApiError(err)
          set({ isLoading: false, error: msg })
          return { success: false, error: msg }
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null })
        try {
          const payload = {
            email: String(data.email || '').trim().toLowerCase(),
            username: String(data.username || '').trim(),
            password: data.password,
            full_name: String(data.full_name || '').trim(),
          }
          const { data: res } = await authApi.register(payload)
          localStorage.setItem('scholara_token', res.access_token)
          set({
            token: res.access_token,
            user: { id: res.user_id, username: res.username, email: res.email },
            isAuthenticated: true,
            isLoading: false,
          })
          return { success: true }
        } catch (err) {
          const msg = formatApiError(err)
          set({ isLoading: false, error: msg })
          return { success: false, error: msg }
        }
      },

      logout: () => {
        localStorage.removeItem('scholara_token')
        localStorage.removeItem('scholara_user')
        set({ user: null, token: null, isAuthenticated: false, error: null })
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'scholara_user',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
