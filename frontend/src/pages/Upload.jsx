import { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  UploadCloud, FileText, Trash2, CheckCircle2,
  AlertCircle, Loader2, RefreshCw, FileType
} from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import { documentApi } from '@/lib/api'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  pending:    { color: 'text-yellow-400', bg: 'bg-yellow-500/10', icon: Loader2, label: 'Pending', spin: true },
  processing: { color: 'text-blue-400',   bg: 'bg-blue-500/10',   icon: Loader2, label: 'Processing...', spin: true },
  ready:      { color: 'text-emerald-400',bg: 'bg-emerald-500/10',icon: CheckCircle2, label: 'Ready', spin: false },
  error:      { color: 'text-red-400',    bg: 'bg-red-500/10',    icon: AlertCircle, label: 'Error', spin: false },
}

function DocumentCard({ doc, onDelete, onRefresh }) {
  const cfg = STATUS_CONFIG[doc.status] || STATUS_CONFIG.pending
  const ext = doc.file_type?.toUpperCase() || 'FILE'
  const size = doc.file_size_bytes ? `${(doc.file_size_bytes / 1024).toFixed(0)} KB` : ''

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4 flex items-start gap-4 group">
      {/* Icon */}
      <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
        <FileType size={18} className="text-indigo-400" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-medium truncate">{doc.original_filename}</p>
        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
          <span className="bg-slate-700/50 px-1.5 py-0.5 rounded text-slate-400 font-mono">{ext}</span>
          {size && <span>{size}</span>}
          {doc.chunk_count > 0 && <span>{doc.chunk_count} chunks</span>}
          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Status */}
      <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg ${cfg.bg} ${cfg.color} flex-shrink-0`}>
        <cfg.icon size={11} className={cfg.spin ? 'animate-spin' : ''} />
        {cfg.label}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        {(doc.status === 'processing' || doc.status === 'pending') && (
          <button onClick={() => onRefresh(doc.id)} className="text-slate-500 hover:text-blue-400 transition-colors">
            <RefreshCw size={14} />
          </button>
        )}
        <button onClick={() => onDelete(doc.id)} className="text-slate-500 hover:text-red-400 transition-colors">
          <Trash2 size={14} />
        </button>
      </div>
    </motion.div>
  )
}

export default function Upload() {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [pollingIds, setPollingIds] = useState(new Set())

  const loadDocuments = async () => {
    try {
      const { data } = await documentApi.list()
      setDocuments(data)
      // Poll docs that are still processing
      const pending = data.filter(d => d.status === 'processing' || d.status === 'pending')
      if (pending.length > 0) {
        setPollingIds(new Set(pending.map(d => d.id)))
      }
    } catch {}
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  // Poll processing documents every 3s
  useEffect(() => {
    if (pollingIds.size === 0) return
    const interval = setInterval(loadDocuments, 3000)
    return () => clearInterval(interval)
  }, [pollingIds])

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      setUploading(true)
      setUploadProgress(0)
      try {
        const { data } = await documentApi.upload(file, setUploadProgress)
        setDocuments(prev => [data, ...prev])
        setPollingIds(prev => new Set([...prev, data.id]))
        toast.success(`"${file.name}" uploaded and processing...`)
      } catch (err) {
        const msg = err.response?.data?.detail || 'Upload failed'
        toast.error(msg)
      } finally {
        setUploading(false)
        setUploadProgress(0)
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: true,
    disabled: uploading,
  })

  const handleDelete = async (id) => {
    if (!confirm('Delete this document and its embeddings?')) return
    try {
      await documentApi.delete(id)
      setDocuments(prev => prev.filter(d => d.id !== id))
      toast.success('Document deleted')
    } catch {
      toast.error('Failed to delete document')
    }
  }

  const handleRefresh = async (id) => {
    try {
      const { data } = await documentApi.get(id)
      setDocuments(prev => prev.map(d => d.id === id ? data : d))
    } catch {}
  }

  const readyCount = documents.filter(d => d.status === 'ready').length

  return (
    <AppLayout>
      <div className="flex-1 overflow-y-auto px-8 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-white mb-1">Research Documents</h1>
          <p className="text-slate-400 text-sm">
            Upload PDFs, DOCX, or TXT files. They'll be chunked and indexed automatically.
            {readyCount > 0 && <span className="text-emerald-400 ml-2">{readyCount} document(s) ready for chat.</span>}
          </p>
        </div>

        {/* Dropzone */}
        <div {...getRootProps()} className={`
          relative rounded-2xl border-2 border-dashed transition-all duration-200 p-12 text-center cursor-pointer mb-8
          ${isDragActive
            ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]'
            : 'border-white/10 hover:border-indigo-500/40 hover:bg-white/2'
          }
          ${uploading ? 'opacity-60 cursor-not-allowed' : ''}
        `}>
          <input {...getInputProps()} />

          <AnimatePresence mode="wait">
            {uploading ? (
              <motion.div key="uploading" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Loader2 size={36} className="text-indigo-400 animate-spin mx-auto mb-4" />
                <p className="text-white font-medium mb-2">Uploading...</p>
                <div className="w-48 mx-auto h-1.5 bg-surface-800 rounded-full overflow-hidden">
                  <motion.div className="h-full bg-indigo-500 rounded-full"
                    initial={{ width: 0 }} animate={{ width: `${uploadProgress}%` }} />
                </div>
                <p className="text-slate-500 text-sm mt-2">{uploadProgress}%</p>
              </motion.div>
            ) : (
              <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <UploadCloud size={40} className={`mx-auto mb-4 ${isDragActive ? 'text-indigo-300' : 'text-slate-500'}`} />
                <p className="text-white font-medium mb-1">
                  {isDragActive ? 'Drop your files here' : 'Drag & drop research papers'}
                </p>
                <p className="text-slate-500 text-sm mb-4">or click to browse files</p>
                <div className="flex items-center justify-center gap-2 text-xs text-slate-600">
                  {['PDF', 'DOCX', 'TXT'].map(t => (
                    <span key={t} className="bg-surface-800 px-2 py-0.5 rounded font-mono">{t}</span>
                  ))}
                  <span>• Max 50MB</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Document list */}
        {documents.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-white">Your Documents ({documents.length})</h2>
              <button onClick={loadDocuments} className="text-slate-500 hover:text-white transition-colors">
                <RefreshCw size={14} />
              </button>
            </div>
            <div className="space-y-2">
              <AnimatePresence>
                {documents.map(doc => (
                  <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} onRefresh={handleRefresh} />
                ))}
              </AnimatePresence>
            </div>
          </div>
        ) : (
          !uploading && (
            <div className="text-center text-slate-600 py-8">
              <FileText size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No documents yet. Upload your first research paper above.</p>
            </div>
          )
        )}
      </div>
    </AppLayout>
  )
}
