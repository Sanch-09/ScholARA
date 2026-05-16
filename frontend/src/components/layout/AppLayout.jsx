import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen, MessageSquare, UploadCloud, BarChart2,
  LayoutDashboard, LogOut, Menu, X, Plus, ChevronRight,
  Trash2
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useChatStore } from '@/store/chatStore'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/upload', icon: UploadCloud, label: 'Documents' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
]

export default function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuthStore()
  const { sessions, deleteSession, createSession, selectSession } = useChatStore()
  const navigate = useNavigate()

  const handleNewChat = async () => {
    const session = await createSession()
    if (session) navigate(`/chat/${session.id}`)
  }

  const handleDeleteSession = async (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    await deleteSession(id)
  }

  return (
    <div className="flex h-screen bg-surface-950 overflow-hidden">
      {/* ── Sidebar ── */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="hidden md:flex flex-col h-full bg-surface-900 border-r border-white/5 relative z-10 flex-shrink-0"
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <BookOpen size={16} className="text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: 'auto' }} exit={{ opacity: 0, width: 0 }}
                className="font-display font-bold text-white whitespace-nowrap overflow-hidden">
                ScholARA
              </motion.span>
            )}
          </AnimatePresence>
          <button onClick={() => setCollapsed(!collapsed)} className="ml-auto text-slate-500 hover:text-white flex-shrink-0">
            <ChevronRight size={16} className={`transition-transform ${collapsed ? '' : 'rotate-180'}`} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon size={17} className="flex-shrink-0" />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="whitespace-nowrap overflow-hidden">
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
            </NavLink>
          ))}

          {/* New Chat button */}
          {!collapsed && (
            <div className="pt-4">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-all border border-indigo-500/20 border-dashed"
              >
                <Plus size={15} /> New Chat
              </button>

              {/* Recent sessions */}
              {sessions.slice(0, 6).map((s) => (
                <NavLink
                  key={s.id}
                  to={`/chat/${s.id}`}
                  onClick={() => selectSession(s.id)}
                  className={({ isActive }) =>
                    `group flex items-center gap-2 px-3 py-2 mt-1 rounded-lg text-xs transition-all ${
                      isActive ? 'bg-white/5 text-white' : 'text-slate-500 hover:text-slate-300 hover:bg-white/3'
                    }`
                  }
                >
                  <MessageSquare size={12} className="flex-shrink-0" />
                  <span className="flex-1 truncate">{s.title}</span>
                  <button
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all"
                  >
                    <Trash2 size={11} />
                  </button>
                </NavLink>
              ))}
            </div>
          )}
        </nav>

        {/* User */}
        <div className="border-t border-white/5 p-3">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate">{user?.username}</p>
                  <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                </motion.div>
              )}
            </AnimatePresence>
            <button onClick={logout} className="text-slate-500 hover:text-red-400 transition-colors flex-shrink-0">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </motion.aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {children}
      </main>
    </div>
  )
}
