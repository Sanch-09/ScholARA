import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  BookOpen, Zap, Brain, Shield, UploadCloud,
  MessageSquare, BarChart2, ArrowRight, Github, Star
} from 'lucide-react'

const features = [
  { icon: Brain, title: 'RAG-Powered Answers', desc: 'Retrieval-Augmented Generation ensures every answer is grounded in your actual research papers.' },
  { icon: UploadCloud, title: 'PDF / DOCX / TXT', desc: 'Upload any academic document. Our pipeline extracts, chunks, and indexes it in seconds.' },
  { icon: MessageSquare, title: 'Multi-turn Memory', desc: 'Maintains conversation context so you can have deep, flowing research dialogues.' },
  { icon: Shield, title: 'Source Citations', desc: 'Every answer cites the exact paper and chunk it came from. No hallucinations.' },
  { icon: Zap, title: 'Streaming Responses', desc: 'See answers appear token-by-token with smooth typing animations.' },
  { icon: BarChart2, title: 'Analytics Dashboard', desc: 'Track your research sessions, document usage, and AI confidence scores.' },
]

const techStack = [
  { name: 'FastAPI', color: '#009688' },
  { name: 'LangChain', color: '#1C3C3C' },
  { name: 'FAISS', color: '#0057e7' },
  { name: 'Ollama', color: '#ffffff' },
  { name: 'React 18', color: '#61DAFB' },
  { name: 'Sentence Transformers', color: '#FF6F00' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-surface-950 overflow-x-hidden">
      {/* Background grid */}
      <div className="fixed inset-0 opacity-[0.03]"
        style={{ backgroundImage: 'linear-gradient(#6366f1 1px, transparent 1px), linear-gradient(90deg, #6366f1 1px, transparent 1px)', backgroundSize: '50px 50px' }}
      />

      {/* Ambient glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] opacity-20"
        style={{ background: 'radial-gradient(ellipse, #4f46e5 0%, transparent 70%)' }}
      />

      {/* ── Navbar ── */}
      <nav className="relative z-50 flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center glow-brand-sm">
            <BookOpen size={18} className="text-white" />
          </div>
          <span className="font-display font-bold text-xl text-white">ScholARA</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#tech" className="hover:text-white transition-colors">Tech Stack</a>
          <a href="#how" className="hover:text-white transition-colors">How It Works</a>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/auth" className="btn-ghost text-sm">Sign In</Link>
          <Link to="/auth" className="btn-primary text-sm flex items-center gap-2">
            Get Started <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative z-10 text-center px-6 pt-20 pb-32 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-indigo-300 mb-8">
            <Star size={13} fill="currentColor" />
            <span>AI Research Assistant — Powered by RAG + LLaMA</span>
          </div>

          <h1 className="font-display text-6xl md:text-7xl font-bold leading-tight text-white mb-6">
            Research Smarter.<br />
            <span className="gradient-text">Ask Your Papers.</span>
          </h1>

          <p className="text-slate-400 text-xl max-w-2xl mx-auto leading-relaxed mb-10">
            Upload research papers and have intelligent conversations with them. 
            ScholARA uses RAG to give you cited, accurate answers — never hallucinated.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/auth"
              className="btn-primary text-base px-8 py-3.5 flex items-center justify-center gap-2 glow-brand">
              Start Researching <ArrowRight size={16} />
            </Link>
            <a href="https://github.com" target="_blank" rel="noreferrer"
              className="btn-ghost text-base px-8 py-3.5 flex items-center justify-center gap-2 glass">
              <Github size={16} /> View on GitHub
            </a>
          </div>
        </motion.div>

        {/* Chat preview mockup */}
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-20 glass rounded-2xl p-6 text-left max-w-2xl mx-auto border border-indigo-500/20"
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-red-500/70" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <div className="w-3 h-3 rounded-full bg-green-500/70" />
            <span className="ml-2 text-slate-500 text-xs font-mono">ScholARA Chat</span>
          </div>

          <div className="space-y-4">
            <div className="flex justify-end">
              <div className="chat-bubble-user text-white text-sm px-4 py-2.5 max-w-xs">
                What methodology did the authors use in this study?
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Brain size={12} className="text-white" />
              </div>
              <div className="chat-bubble-assistant text-slate-200 text-sm px-4 py-2.5 max-w-sm">
                The authors employed a <strong className="text-indigo-300">mixed-methods approach</strong>, 
                combining quantitative surveys (n=450) with qualitative interviews.
                <div className="mt-2 text-xs text-indigo-400 flex items-center gap-1">
                  <Shield size={10} /> Source: paper.pdf, chunk 3
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="relative z-10 px-6 py-24 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-4xl font-bold text-white mb-4">
            Everything You Need
          </h2>
          <p className="text-slate-400 text-lg">Built for serious researchers, students, and academics.</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feat, i) => (
            <motion.div
              key={feat.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="glass glass-hover rounded-2xl p-6 group"
            >
              <div className="w-11 h-11 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-4 group-hover:bg-indigo-500/20 transition-colors">
                <feat.icon size={20} className="text-indigo-400" />
              </div>
              <h3 className="font-display font-semibold text-white mb-2">{feat.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how" className="relative z-10 px-6 py-24 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="font-display text-4xl font-bold text-white mb-4">How RAG Works</h2>
          <p className="text-slate-400 text-lg">A 7-step pipeline from document to answer.</p>
        </motion.div>

        <div className="relative">
          <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-indigo-500/50 to-transparent" />
          {[
            ['Upload', 'You upload your PDF, DOCX, or TXT research paper'],
            ['Parse', 'PyMuPDF extracts clean text, preserving page structure'],
            ['Chunk', 'Text is split into 500-char overlapping chunks'],
            ['Embed', 'Sentence-Transformers converts each chunk to a 384-dim vector'],
            ['Store', 'Vectors stored in FAISS index on disk'],
            ['Retrieve', 'Your query is embedded → cosine similarity search → top-5 chunks'],
            ['Generate', 'LLaMA receives your query + context → cited answer'],
          ].map(([title, desc], i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-6 mb-8"
            >
              <div className="w-16 h-16 rounded-full glass border border-indigo-500/30 flex items-center justify-center flex-shrink-0 relative z-10">
                <span className="font-display font-bold text-indigo-400">{i + 1}</span>
              </div>
              <div className="pt-4">
                <h3 className="font-semibold text-white mb-1">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Tech Stack ── */}
      <section id="tech" className="relative z-10 px-6 py-16 max-w-4xl mx-auto text-center">
        <h2 className="font-display text-2xl font-bold text-white mb-8">100% Free & Open-Source Stack</h2>
        <div className="flex flex-wrap justify-center gap-3">
          {techStack.map((t) => (
            <span key={t.name} className="glass px-4 py-2 rounded-xl text-sm text-slate-300">
              {t.name}
            </span>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="relative z-10 px-6 py-24 text-center max-w-3xl mx-auto">
        <div className="glass rounded-3xl p-12 border border-indigo-500/20">
          <h2 className="font-display text-4xl font-bold text-white mb-4">
            Ready to Research Smarter?
          </h2>
          <p className="text-slate-400 mb-8">Upload your first paper and get answers in minutes.</p>
          <Link to="/auth" className="btn-primary text-lg px-10 py-4 inline-flex items-center gap-2 glow-brand">
            Get Started Free <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t border-white/5 px-6 py-8 text-center text-slate-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <BookOpen size={14} className="text-indigo-400" />
          <span className="font-display font-semibold text-white">ScholARA</span>
        </div>
        <p>Built for university mini-capstone • Track A: Domain-Specific Chatbot</p>
      </footer>
    </div>
  )
}
