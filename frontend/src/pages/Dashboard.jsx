import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  MessageSquare, UploadCloud, FileText, BarChart2,
  Plus, ArrowRight, Brain, Zap, Clock
} from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import { useAuthStore } from '@/store/authStore'
import { useChatStore } from '@/store/chatStore'
import { analyticsApi } from '@/lib/api'

export default function Dashboard() {
  const { user } = useAuthStore()
  const { sessions, fetchSessions, createSession } = useChatStore()
  const [analytics, setAnalytics] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchSessions()
    analyticsApi.summary().then(r => setAnalytics(r.data)).catch(() => {})
  }, [])

  const handleNewChat = async () => {
    const session = await createSession()
    if (session) navigate(`/chat/${session.id}`)
  }

  const stats = [
    { label: 'Documents', value: analytics?.documents?.total ?? '—', icon: FileText, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Chat Sessions', value: analytics?.sessions?.total ?? '—', icon: MessageSquare, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
    { label: 'Queries Asked', value: analytics?.messages?.queries ?? '—', icon: Brain, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Avg Confidence', value: analytics?.avg_confidence ? `${Math.round(analytics.avg_confidence * 100)}%` : '—', icon: Zap, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ]

  return (
    <AppLayout>
      <div className="flex-1 overflow-y-auto px-8 py-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display text-3xl font-bold text-white">
            Good day, <span className="gradient-text">{user?.username}</span> 👋
          </h1>
          <p className="text-slate-400 mt-1">Here's an overview of your research activity.</p>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((s, i) => (
            <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
              className="glass rounded-2xl p-5">
              <div className={`w-10 h-10 ${s.bg} rounded-xl flex items-center justify-center mb-3`}>
                <s.icon size={18} className={s.color} />
              </div>
              <p className="text-2xl font-display font-bold text-white">{s.value}</p>
              <p className="text-sm text-slate-400 mt-0.5">{s.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            onClick={handleNewChat}
            className="glass glass-hover rounded-2xl p-6 text-left group border border-indigo-500/20 hover:border-indigo-500/40 transition-all">
            <div className="w-11 h-11 bg-indigo-500/15 rounded-xl flex items-center justify-center mb-4 group-hover:bg-indigo-500/25 transition-colors">
              <Plus size={20} className="text-indigo-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">New Chat Session</h3>
            <p className="text-slate-400 text-sm">Start a conversation with your papers</p>
          </motion.button>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
            <Link to="/upload" className="block glass glass-hover rounded-2xl p-6 text-left group border border-blue-500/20 hover:border-blue-500/40 transition-all h-full">
              <div className="w-11 h-11 bg-blue-500/15 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-500/25 transition-colors">
                <UploadCloud size={20} className="text-blue-400" />
              </div>
              <h3 className="font-semibold text-white mb-1">Upload Document</h3>
              <p className="text-slate-400 text-sm">Add PDF, DOCX, or TXT papers</p>
            </Link>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            <Link to="/analytics" className="block glass glass-hover rounded-2xl p-6 text-left group border border-emerald-500/20 hover:border-emerald-500/40 transition-all h-full">
              <div className="w-11 h-11 bg-emerald-500/15 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/25 transition-colors">
                <BarChart2 size={20} className="text-emerald-400" />
              </div>
              <h3 className="font-semibold text-white mb-1">View Analytics</h3>
              <p className="text-slate-400 text-sm">Track research usage & metrics</p>
            </Link>
          </motion.div>
        </div>

        {/* Recent sessions */}
        {sessions.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-white">Recent Chats</h2>
              <Link to="/chat" className="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                View all <ArrowRight size={13} />
              </Link>
            </div>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((s) => (
                <Link key={s.id} to={`/chat/${s.id}`}
                  className="flex items-center gap-3 glass glass-hover rounded-xl px-4 py-3 group">
                  <MessageSquare size={15} className="text-indigo-400 flex-shrink-0" />
                  <span className="text-slate-300 text-sm flex-1 truncate">{s.title}</span>
                  <span className="text-slate-600 text-xs flex items-center gap-1">
                    <Clock size={11} />
                    {new Date(s.updated_at).toLocaleDateString()}
                  </span>
                  <ArrowRight size={13} className="text-slate-600 group-hover:text-indigo-400 transition-colors" />
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </AppLayout>
  )
}
