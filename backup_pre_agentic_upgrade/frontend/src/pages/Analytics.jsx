import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart2, FileText, MessageSquare, Brain, ThumbsUp,
  ThumbsDown, Zap, Database, RefreshCw, TrendingUp
} from 'lucide-react'
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell
} from 'recharts'
import AppLayout from '@/components/layout/AppLayout'
import { analyticsApi } from '@/lib/api'

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981']

function StatCard({ icon: Icon, label, value, sub, color = 'text-indigo-400', bg = 'bg-indigo-500/10', delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="glass rounded-2xl p-5">
      <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-3`}>
        <Icon size={18} className={color} />
      </div>
      <p className="text-2xl font-display font-bold text-white">{value ?? '—'}</p>
      <p className="text-sm text-slate-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </motion.div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="glass rounded-xl px-3 py-2 text-xs border border-white/10">
        <p className="text-slate-400">{label}</p>
        <p className="text-white font-semibold">{payload[0].value}</p>
      </div>
    )
  }
  return null
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const { data: res } = await analyticsApi.summary()
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const barData = data ? [
    { name: 'Documents', value: data.documents.total },
    { name: 'Sessions', value: data.sessions.total },
    { name: 'Queries', value: data.messages.queries },
    { name: 'Chunks', value: Math.round((data.documents.total_chunks || 0) / 10) },
  ] : []

  const feedbackData = data ? [
    { name: 'Positive', value: data.feedback.positive, fill: '#10b981' },
    { name: 'Negative', value: data.feedback.negative, fill: '#ef4444' },
  ] : []

  const confidenceVal = data?.avg_confidence
    ? Math.round(data.avg_confidence * 100)
    : 0

  return (
    <AppLayout>
      <div className="flex-1 overflow-y-auto px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold text-white">Analytics</h1>
            <p className="text-slate-400 text-sm mt-1">Your research activity at a glance</p>
          </div>
          <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-500 text-sm flex items-center gap-2">
              <RefreshCw size={16} className="animate-spin" /> Loading analytics...
            </div>
          </div>
        ) : (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard icon={FileText} label="Documents Uploaded" value={data?.documents?.total}
                sub={`${data?.documents?.ready} ready`} delay={0} />
              <StatCard icon={MessageSquare} label="Chat Sessions" value={data?.sessions?.total}
                color="text-purple-400" bg="bg-purple-500/10" delay={0.08} />
              <StatCard icon={Brain} label="Total Queries" value={data?.messages?.queries}
                color="text-blue-400" bg="bg-blue-500/10" delay={0.16} />
              <StatCard icon={Database} label="Indexed Chunks" value={data?.documents?.total_chunks}
                color="text-emerald-400" bg="bg-emerald-500/10" delay={0.24} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Bar chart */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                className="glass rounded-2xl p-5 lg:col-span-2">
                <h2 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp size={16} className="text-indigo-400" /> Usage Overview
                </h2>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.05)' }} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {barData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </motion.div>

              {/* Confidence gauge */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
                className="glass rounded-2xl p-5">
                <h2 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap size={16} className="text-indigo-400" /> Avg Confidence
                </h2>
                <div className="relative">
                  <ResponsiveContainer width="100%" height={160}>
                    <RadialBarChart cx="50%" cy="60%" innerRadius="60%" outerRadius="90%"
                      data={[{ value: confidenceVal, fill: '#6366f1' }]} startAngle={180} endAngle={0}>
                      <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#1e293b' }} />
                    </RadialBarChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-end justify-center pb-4">
                    <div className="text-center">
                      <p className="text-3xl font-display font-bold text-white">{confidenceVal}%</p>
                      <p className="text-xs text-slate-500">confidence</p>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-slate-500 text-center mt-2">
                  Based on retrieval similarity scores
                </p>
              </motion.div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feedback */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                className="glass rounded-2xl p-5">
                <h2 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
                  <ThumbsUp size={16} className="text-indigo-400" /> Response Feedback
                </h2>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                      <ThumbsUp size={14} className="text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-xl font-bold text-white">{data?.feedback?.positive ?? 0}</p>
                      <p className="text-xs text-slate-500">Positive</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-red-500/10 rounded-lg flex items-center justify-center">
                      <ThumbsDown size={14} className="text-red-400" />
                    </div>
                    <div>
                      <p className="text-xl font-bold text-white">{data?.feedback?.negative ?? 0}</p>
                      <p className="text-xs text-slate-500">Negative</p>
                    </div>
                  </div>
                  {data?.feedback?.satisfaction_rate != null && (
                    <div className="ml-auto text-right">
                      <p className="text-2xl font-display font-bold text-emerald-400">
                        {data.feedback.satisfaction_rate}%
                      </p>
                      <p className="text-xs text-slate-500">satisfaction</p>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Vector DB stats */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
                className="glass rounded-2xl p-5">
                <h2 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
                  <Database size={16} className="text-indigo-400" /> Vector Database
                </h2>
                <div className="space-y-3">
                  {[
                    ['Total Vectors', data?.vector_db?.total_vectors ?? 0],
                    ['Embedding Dim', data?.vector_db?.embedding_dim ?? 384],
                    ['Model', data?.vector_db?.model ?? 'all-MiniLM-L6-v2'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">{k}</span>
                      <span className="text-white font-mono text-xs bg-surface-800 px-2 py-0.5 rounded">{v}</span>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Recent sessions */}
              {data?.recent_sessions?.length > 0 && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                  className="glass rounded-2xl p-5 lg:col-span-2">
                  <h2 className="font-display font-semibold text-white mb-4 flex items-center gap-2">
                    <MessageSquare size={16} className="text-indigo-400" /> Recent Sessions
                  </h2>
                  <div className="space-y-2">
                    {data.recent_sessions.map((s, i) => (
                      <div key={s.id} className="flex items-center gap-3 text-sm py-2 border-b border-white/5 last:border-0">
                        <span className="text-slate-600 w-5 text-xs">{i + 1}</span>
                        <span className="text-slate-300 flex-1 truncate">{s.title}</span>
                        <span className="text-slate-600 text-xs">
                          {new Date(s.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>
          </>
        )}
      </div>
    </AppLayout>
  )
}
