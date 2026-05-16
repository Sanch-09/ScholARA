import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Plus, Brain, ThumbsUp, ThumbsDown, Copy,
  ChevronDown, FileText, Sparkles, Loader2
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AppLayout from '@/components/layout/AppLayout'
import { useChatStore } from '@/store/chatStore'
import { documentApi } from '@/lib/api'
import toast from 'react-hot-toast'

const SUGGESTED_PROMPTS = [
  'What is the main research contribution of this paper?',
  'Summarize the methodology used in this study.',
  'What are the key findings and conclusions?',
  'What limitations do the authors acknowledge?',
  'How does this compare to related work?',
  'What future work do the authors suggest?',
]

function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
        <Brain size={13} className="text-white" />
      </div>
      <div className="chat-bubble-assistant px-4 py-3 flex items-center gap-1.5">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  )
}

function MessageBubble({ msg, onFeedback }) {
  const [copied, setCopied] = useState(false)
  const sources = (() => {
    if (!msg.sources) return []
    if (typeof msg.sources !== 'string') return Array.isArray(msg.sources) ? msg.sources : []
    try {
      const parsed = JSON.parse(msg.sources)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  })()

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (msg.role === 'user') {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
        <div className="chat-bubble-user text-white px-4 py-3 max-w-[75%] text-sm leading-relaxed">
          {msg.content}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3 group">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain size={13} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="chat-bubble-assistant px-4 py-3 max-w-[85%] text-sm leading-relaxed">
          <div className="markdown-body text-slate-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
          </div>
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {sources.map((s, i) => (
              <div key={i} className="inline-flex items-center gap-1.5 text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-lg">
                <FileText size={10} />
                <span className="truncate max-w-[140px]">{s.filename}</span>
                <span className="text-indigo-500">·</span>
                <span>chunk {s.chunk_index + 1}</span>
              </div>
            ))}
          </div>
        )}

        {/* Confidence + actions */}
        <div className="mt-2 flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
          {msg.confidence != null && (
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Sparkles size={10} />
              {Math.round(msg.confidence * 100)}% confidence
            </span>
          )}
          <button onClick={handleCopy} className="text-slate-600 hover:text-slate-300 text-xs flex items-center gap-1 transition-colors">
            <Copy size={11} /> {copied ? 'Copied!' : 'Copy'}
          </button>
          {msg.id && (
            <>
              <button onClick={() => onFeedback(msg.id, 'positive')}
                className={`text-xs flex items-center gap-1 transition-colors ${msg.feedback === 'positive' ? 'text-emerald-400' : 'text-slate-600 hover:text-emerald-400'}`}>
                <ThumbsUp size={11} />
              </button>
              <button onClick={() => onFeedback(msg.id, 'negative')}
                className={`text-xs flex items-center gap-1 transition-colors ${msg.feedback === 'negative' ? 'text-red-400' : 'text-slate-600 hover:text-red-400'}`}>
                <ThumbsDown size={11} />
              </button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default function Chat() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [documents, setDocuments] = useState([])
  const [selectedDocs, setSelectedDocs] = useState([])
  const [showDocPicker, setShowDocPicker] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const {
    messages, currentSession, isStreaming, streamingContent,
    sendMessage, submitFeedback, createSession, selectSession, fetchSessions, error
  } = useChatStore()

  // Load session or create new
  useEffect(() => {
    fetchSessions()
    if (sessionId) {
      selectSession(parseInt(sessionId))
    }
  }, [sessionId])

  // Load user documents
  useEffect(() => {
    documentApi.list().then(r => {
      const ready = r.data.filter(d => d.status === 'ready')
      setDocuments(ready)
    }).catch(() => {})
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = async () => {
    const q = input.trim()
    if (!q || isStreaming) return

    let session = currentSession
    if (!session) {
      session = await createSession(selectedDocs)
      if (session) navigate(`/chat/${session.id}`, { replace: true })
    }

    setInput('')
    await sendMessage(q, selectedDocs)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleDoc = (id) => {
    setSelectedDocs(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  const isEmpty = messages.length === 0 && !isStreaming

  return (
    <AppLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
          <Brain size={18} className="text-indigo-400" />
          <h1 className="font-display font-semibold text-white">
            {currentSession?.title || 'New Chat'}
          </h1>
          {documents.length > 0 && (
            <div className="ml-auto">
              <button
                onClick={() => setShowDocPicker(!showDocPicker)}
                className="flex items-center gap-2 text-xs glass px-3 py-1.5 rounded-lg text-slate-300 hover:text-white transition-colors"
              >
                <FileText size={12} />
                {selectedDocs.length > 0 ? `${selectedDocs.length} doc(s) selected` : 'Select documents'}
                <ChevronDown size={12} className={`transition-transform ${showDocPicker ? 'rotate-180' : ''}`} />
              </button>
              <AnimatePresence>
                {showDocPicker && (
                  <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                    className="absolute right-6 mt-2 w-64 glass rounded-xl p-3 z-50 border border-white/10 shadow-2xl">
                    <p className="text-xs text-slate-500 mb-2 font-medium">Filter by document</p>
                    {documents.map(doc => (
                      <label key={doc.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
                        <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDoc(doc.id)}
                          className="accent-indigo-500" />
                        <span className="text-xs text-slate-300 truncate">{doc.original_filename}</span>
                      </label>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {isEmpty && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20 flex items-center justify-center mb-4">
                <Brain size={28} className="text-indigo-400" />
              </div>
              <h2 className="font-display text-xl font-semibold text-white mb-2">Ask ScholARA</h2>
              <p className="text-slate-500 text-sm max-w-xs mb-8">
                Upload a research paper and ask questions. I'll answer with citations.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button key={p} onClick={() => { setInput(p); inputRef.current?.focus() }}
                    className="text-left text-xs glass glass-hover rounded-xl px-3 py-2.5 text-slate-400 hover:text-white transition-all">
                    {p}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} onFeedback={submitFeedback} />
          ))}

          {/* Streaming message */}
          {isStreaming && (
            streamingContent
              ? (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain size={13} className="text-white" />
                  </div>
                  <div className="chat-bubble-assistant px-4 py-3 max-w-[85%] text-sm leading-relaxed">
                    <div className="markdown-body text-slate-200">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                    </div>
                    <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-0.5 animate-pulse" />
                  </div>
                </motion.div>
              )
              : <TypingIndicator />
          )}

          {error && (
            <div className="text-center text-sm text-red-400 bg-red-500/10 rounded-xl p-3">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-6 py-4 border-t border-white/5">
          <div className="flex gap-3 items-end">
            <div className="flex-1 glass rounded-2xl border border-white/10 focus-within:border-indigo-500/50 transition-colors">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your research papers..."
                rows={1}
                className="w-full bg-transparent px-4 py-3 text-sm text-white placeholder-slate-600 resize-none focus:outline-none max-h-32 leading-relaxed"
                style={{ minHeight: '48px' }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="w-11 h-11 rounded-xl btn-primary flex items-center justify-center flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isStreaming
                ? <Loader2 size={16} className="animate-spin" />
                : <Send size={16} />
              }
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2 text-center">
            Press Enter to send • Shift+Enter for newline
          </p>
        </div>
      </div>
    </AppLayout>
  )
}
