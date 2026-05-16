import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate, Link } from 'react-router-dom'
import { BookOpen, Eye, EyeOff, ArrowLeft, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

export default function Auth() {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [showPass, setShowPass] = useState(false)
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' })

  const { login, register, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    clearError()
  }, [mode, clearError])

  const handleSubmit = async (e) => {
    e.preventDefault()

    const fn = mode === 'login' ? login : register
    const result = await fn(form)

    if (result.success) {
      toast.success(mode === 'login' ? 'Welcome back!' : 'Account created!')
      navigate('/dashboard')
    } else {
      toast.error(result.error || 'Something went wrong')
    }
  }

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 opacity-[0.04]"
        style={{ backgroundImage: 'radial-gradient(circle, #6366f1 1px, transparent 1px)', backgroundSize: '30px 30px' }}
      />
      <div className="fixed top-0 right-0 w-96 h-96 opacity-10"
        style={{ background: 'radial-gradient(circle, #818cf8, transparent 70%)' }}
      />

      <div className="w-full max-w-md relative z-10">
        {/* Back link */}
        <Link to="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-8 transition-colors">
          <ArrowLeft size={14} /> Back to home
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-8"
        >
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <BookOpen size={18} className="text-white" />
            </div>
            <span className="font-display font-bold text-xl text-white">ScholARA</span>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 p-1 bg-surface-900 rounded-xl mb-8">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  mode === m
                    ? 'bg-indigo-600 text-white shadow-lg'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.form
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -10 : 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onSubmit={handleSubmit}
              className="space-y-4"
            >
              {mode === 'register' && (
                <>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5">Full Name</label>
                    <input
                      type="text"
                      placeholder="John Doe"
                      value={form.full_name}
                      onChange={update('full_name')}
                      className="w-full bg-surface-900 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5">Username</label>
                    <input
                      type="text"
                      placeholder="researcher42"
                      value={form.username}
                      onChange={update('username')}
                      required
                      className="w-full bg-surface-900 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm text-slate-400 mb-1.5">
                  {mode === 'login' ? 'Email or Username' : 'Email'}
                </label>
                <input
                  type={mode === 'register' ? 'email' : 'text'}
                  placeholder={mode === 'login' ? 'email@example.com or username' : 'email@example.com'}
                  value={form.email}
                  onChange={update('email')}
                  required
                  className="w-full bg-surface-900 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={form.password}
                    onChange={update('password')}
                    required
                    minLength={6}
                    className="w-full bg-surface-900 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-indigo-500 transition-colors pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary py-3.5 text-sm font-semibold flex items-center justify-center gap-2 mt-2"
              >
                {isLoading ? (
                  <><Loader2 size={16} className="animate-spin" /> Processing...</>
                ) : mode === 'login' ? (
                  'Sign In to ScholARA'
                ) : (
                  'Create Account'
                )}
              </button>
            </motion.form>
          </AnimatePresence>

          {/* Demo credentials hint */}
          {mode === 'login' && (
            <div className="mt-4 p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl">
              <p className="text-xs text-slate-500 text-center">
                New here? <button onClick={() => setMode('register')} className="text-indigo-400 hover:text-indigo-300">Create a free account</button>
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
