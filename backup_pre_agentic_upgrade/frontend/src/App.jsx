import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'

import Landing from '@/pages/Landing'
import Auth from '@/pages/Auth'
import Dashboard from '@/pages/Dashboard'
import Chat from '@/pages/Chat'
import Upload from '@/pages/Upload'
import Analytics from '@/pages/Analytics'

function AuthBootstrap({ children }) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false

    const runBootstrap = async () => {
      await useAuthStore.getState().bootstrapAuth()
      if (!cancelled) setReady(true)
    }

    if (useAuthStore.persist.hasHydrated()) {
      runBootstrap()
    }

    const unsub = useAuthStore.persist.onFinishHydration(() => {
      runBootstrap()
    })

    return () => {
      cancelled = true
      unsub?.()
    }
  }, [])

  if (!ready) {
    return (
      <div className="min-h-screen bg-surface-950 flex items-center justify-center">
        <div
          className="w-10 h-10 rounded-xl border-2 border-indigo-500/30 border-t-indigo-500 animate-spin"
          aria-label="Loading"
        />
      </div>
    )
  }

  return children
}

// ── Protected Route ───────────────────────────────────────────
function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/auth" replace />
}

// ── Public Route (redirect if logged in) ─────────────────────
function PublicRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthBootstrap>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: '12px',
            },
            success: { iconTheme: { primary: '#6366f1', secondary: '#fff' } },
          }}
        />

        <Routes>
          {/* Public */}
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<PublicRoute><Auth /></PublicRoute>} />

          {/* Protected */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/chat/:sessionId" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthBootstrap>
    </BrowserRouter>
  )
}
