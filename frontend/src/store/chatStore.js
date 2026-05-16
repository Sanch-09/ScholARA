/**
 * ScholARA — Chat Store (Zustand)
 */

import { create } from 'zustand'
import { chatApi, streamMessage } from '@/lib/api'

export const useChatStore = create((set, get) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  error: null,

  // ── Sessions ──────────────────────────────────────────────

  fetchSessions: async () => {
    try {
      const { data } = await chatApi.listSessions()
      set({ sessions: data })
    } catch (err) {
      console.error('Failed to fetch sessions', err)
    }
  },

  createSession: async (documentIds = []) => {
    try {
      const { data } = await chatApi.createSession({
        title: 'New Chat',
        document_ids: documentIds,
      })
      set((state) => ({
        sessions: [data, ...state.sessions],
        currentSession: data,
        messages: [],
      }))
      return data
    } catch (err) {
      console.error('Failed to create session', err)
    }
  },

  selectSession: async (sessionId) => {
    try {
      const { data } = await chatApi.getSession(sessionId)
      set({
        currentSession: data,
        messages: data.messages || [],
      })
    } catch (err) {
      console.error('Failed to load session', err)
    }
  },

  deleteSession: async (sessionId) => {
    try {
      await chatApi.deleteSession(sessionId)
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
        messages: state.currentSession?.id === sessionId ? [] : state.messages,
      }))
    } catch (err) {
      console.error('Failed to delete session', err)
    }
  },

  // ── Messages ──────────────────────────────────────────────

  sendMessage: async (query, documentIds = []) => {
    const { currentSession } = get()
    if (!currentSession) return

    // Optimistically add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    }
    set((state) => ({
      messages: [...state.messages, userMsg],
      isStreaming: true,
      streamingContent: '',
      error: null,
    }))

    // Stream response
    let fullContent = ''
    let metadata = null

    await streamMessage(
      {
        session_id: currentSession.id,
        query,
        document_ids: documentIds,
      },
      (token) => {
        fullContent += token
        set({ streamingContent: fullContent })
      },
      (meta) => {
        metadata = meta
        // Add final assistant message
        const assistantMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: fullContent,
          sources: meta?.sources || [],
          confidence: meta?.confidence || null,
          created_at: new Date().toISOString(),
        }
        set((state) => ({
          messages: [...state.messages, assistantMsg],
          isStreaming: false,
          streamingContent: '',
        }))

        // Update session title in sidebar
        if (currentSession.title === 'New Chat') {
          set((state) => ({
            sessions: state.sessions.map((s) =>
              s.id === currentSession.id
                ? { ...s, title: query.slice(0, 50) }
                : s
            ),
            currentSession: { ...state.currentSession, title: query.slice(0, 50) },
          }))
        }
      },
      (err) => {
        set({
          isStreaming: false,
          streamingContent: '',
          error: 'Failed to get response. Is the backend running?',
        })
        console.error('Stream error:', err)
      }
    )
  },

  submitFeedback: async (messageId, feedback) => {
    try {
      await chatApi.submitFeedback({ message_id: messageId, feedback })
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === messageId ? { ...m, feedback } : m
        ),
      }))
    } catch (err) {
      console.error('Feedback error', err)
    }
  },

  clearError: () => set({ error: null }),
}))
