/**
 * ScholARA — API Client
 * Axios instance with JWT auth interceptor
 */

import axios from 'axios'

/** In dev, empty baseURL uses Vite proxy (same origin → no CORS). */
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_URL
  if (raw !== undefined && raw !== null && String(raw).trim() !== '') {
    return String(raw).trim().replace(/\/$/, '')
  }
  return import.meta.env.DEV ? '' : 'http://localhost:8000'
}

export const BASE_URL = resolveApiBase()

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/** Normalize FastAPI / Axios error payloads for user-visible messages */
export function formatApiError(error) {
  const d = error?.response?.data?.detail
  if (d == null) {
    return error?.message || 'Request failed'
  }
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d
      .map((x) =>
        typeof x === 'string' ? x : x?.msg || x?.message || JSON.stringify(x)
      )
      .filter(Boolean)
      .join(' ')
  }
  if (typeof d === 'object' && d.msg) return d.msg
  return String(d)
}

// ── Request interceptor: attach JWT ──────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('scholara_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor: handle 401 ─────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const reqUrl = error.config?.url || ''
    const isAuthForm =
      reqUrl.includes('/auth/login') || reqUrl.includes('/auth/register')
    const skipRedirect = error.config?.skipAuthRedirect === true
    if (status === 401 && !isAuthForm && !skipRedirect) {
      localStorage.removeItem('scholara_token')
      localStorage.removeItem('scholara_user')
      if (!window.location.pathname.startsWith('/auth')) {
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)

// ── Auth APIs ─────────────────────────────────────────────────
// Both login and register send plain JSON - no form-data needed
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) =>
    api.post('/auth/login', {
      email: data.email || data.username,
      password: data.password,
    }),
  me: () => api.get('/auth/me', { skipAuthRedirect: true }),
}

// ── Document APIs ─────────────────────────────────────────────
export const documentApi = {
  upload: (file, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
  },
  list: () => api.get('/documents/'),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
}

// ── Chat APIs ─────────────────────────────────────────────────
export const chatApi = {
  createSession: (data) => api.post('/chat/sessions', data),
  listSessions: () => api.get('/chat/sessions'),
  getSession: (id) => api.get(`/chat/sessions/${id}`),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}`),
  sendMessage: (data) => api.post('/chat/message', data),
  submitFeedback: (data) => api.post('/chat/feedback', data),
}

// ── Analytics APIs ────────────────────────────────────────────
export const analyticsApi = {
  summary: () => api.get('/analytics/summary'),
}

// ── Streaming helper ──────────────────────────────────────────
export const streamMessage = async (data, onToken, onComplete, onError) => {
  const token = localStorage.getItem('scholara_token')
  try {
    const response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let metadata = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.slice(6))
            const tokenText = json.token || ''
            if (tokenText.includes('[METADATA]')) {
              const parts = tokenText.split('[METADATA]')
              if (parts[0]) onToken(parts[0])
              try { metadata = JSON.parse(parts[1]) } catch {}
            } else {
              onToken(tokenText)
            }
          } catch {}
        }
      }
    }

    onComplete(metadata)
  } catch (err) {
    onError(err)
  }
}
