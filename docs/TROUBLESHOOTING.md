# ScholARA — Troubleshooting Guide

---

## 🔴 Backend Issues

### "Connection refused" on port 8000
```bash
# Make sure you're in the project root and venv is active
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

python -m backend.main
# Should print: Uvicorn running on http://0.0.0.0:8000
```

### "ModuleNotFoundError: No module named 'backend'"
```bash
# Run from the project ROOT (scholara/), not from backend/
cd /path/to/scholara
python -m backend.main
```

### "pydantic_settings not found"
```bash
pip install pydantic-settings
```

### Database errors on startup
```bash
# Delete and recreate the database
rm scholara.db
python -m backend.main   # Will recreate tables automatically
```

---

## 🔴 Ollama / LLM Issues

### "Ollama is not running"
```bash
# Start Ollama in a separate terminal
ollama serve

# Check it's working
curl http://localhost:11434/api/tags
```

### "Model not found" / slow first response
```bash
# Pull the model (one-time download ~2GB)
ollama pull llama3.2

# Verify it's downloaded
ollama list

# Alternative smaller models if RAM is limited:
ollama pull phi3        # ~1.5GB, good quality
ollama pull gemma2:2b   # ~1.6GB, fast
ollama pull tinyllama   # ~600MB, basic quality

# Update .env to match:
OLLAMA_MODEL=phi3
```

### Ollama responds but answers are very slow
- Normal first response: 10–30 seconds (model loading)
- Subsequent responses: 3–8 seconds
- If consistently slow: use a smaller model (phi3 instead of llama3.2)
- Ensure you have 8GB+ RAM; close other applications

### On Windows: "ollama is not recognized"
- Reinstall Ollama from https://ollama.ai and restart terminal

---

## 🔴 Embedding / FAISS Issues

### "No module named 'faiss'"
```bash
pip install faiss-cpu    # CPU version (free, works everywhere)
# NOT faiss-gpu (requires CUDA)
```

### "FAISS index is empty" error in chat
- You need to upload at least one document first
- Go to /upload and upload a PDF/DOCX/TXT
- Wait for status to change to "Ready" (green)
- Then go to /chat

### Embedding model download hangs
```bash
# First run downloads ~90MB model — needs internet
# Check your internet connection
# Proxy? Set HF_ENDPOINT environment variable

# Force re-download:
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

---

## 🔴 Frontend Issues

### "npm install" fails
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Vite proxy not working (API calls fail)
- Make sure backend is running on port 8000
- Check `vite.config.js` proxy settings
- Try accessing http://localhost:8000/docs directly

### "Cannot read properties of null" in React
- Usually a state issue — refresh the page
- Clear localStorage: open DevTools → Application → Local Storage → Clear all

### Login works but auth persists after logout
```bash
# Clear browser storage
# DevTools → Application → Local Storage → Delete "scholara_user"
```

---

## 🔴 Document Upload Issues

### "Unsupported file type" error
- Supported: `.pdf`, `.docx`, `.doc`, `.txt` only
- Make sure file extension is correct

### Document stuck in "Processing" state
```bash
# Check backend logs for error
# The logs appear in the terminal running python -m backend.main

# Check document status via API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/documents/
```

### PDF text extraction returns empty
- Some PDFs are image-based scans — PyMuPDF can't extract text from images
- Solution: use a PDF with actual text content, or OCR first
- Test with the included `docs/sample_paper.txt`

### Large PDF upload times out
- Default max: 50MB in `.env` (`MAX_FILE_SIZE_MB`)
- For large files, increase timeout in `frontend/src/lib/api.js` (line: `timeout: 30000`)

---

## 🔴 Port Conflicts

### Port 8000 already in use
```bash
# Find and kill the process
lsof -i :8000          # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Or change port in .env:
BACKEND_PORT=8001
# And update vite.config.js proxy port
```

### Port 5173 already in use
```bash
# Vite will auto-try 5174, 5175...
# Or specify:
cd frontend && npm run dev -- --port 3000
```

---

## 🔴 RAM / Performance Issues

### System running slow with Ollama
```bash
# Use a smaller model
ollama pull phi3        # More RAM efficient
# Edit .env: OLLAMA_MODEL=phi3

# Reduce context in LLM service
# backend/services/llm_service.py → "num_predict": 512 (default 1024)
```

### FAISS uses too much RAM
```bash
# Reduce TOP_K_RETRIEVAL in .env
TOP_K_RETRIEVAL=3   # Default is 5
```

---

## ✅ Quick Health Check

Run these commands to verify everything works:

```bash
# 1. Backend health
curl http://localhost:8000/health

# 2. Backend docs
open http://localhost:8000/docs   # Mac
start http://localhost:8000/docs  # Windows

# 3. Ollama
curl http://localhost:11434/api/tags

# 4. Test RAG pipeline
python rag_pipeline/pipeline.py docs/sample_paper.txt "What is the main contribution?"

# 5. Frontend
open http://localhost:5173
```

---

## 📞 Getting Help

1. Check the backend terminal for Python error messages
2. Check browser Console (F12) for frontend errors
3. Check the FastAPI docs at http://localhost:8000/docs — you can test APIs directly there
4. Common Python errors: always check you have the venv activated and are in the project root
