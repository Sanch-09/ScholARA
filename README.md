# 🎓 ScholARA — AI Research Paper Assistant

> A domain-specific RAG-powered AI chatbot for academic research, built as a university mini-capstone project.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat&logo=react)](https://reactjs.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.1-1C3C3C?style=flat)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Project Overview

**ScholARA** is an intelligent academic research assistant that enables students and researchers to:
- Upload research papers (PDF, DOCX, TXT)
- Ask domain-specific questions about uploaded documents
- Receive cited, accurate answers powered by RAG
- Maintain multi-turn conversation memory
- Track session analytics

---

## 🏗️ Architecture

```
User → React Frontend (Vite + Tailwind)
         ↓
      FastAPI Backend
         ↓
   Document Ingestion Pipeline
         ↓
   Chunking + Sentence Transformer Embeddings
         ↓
      FAISS Vector Database
         ↓
   Semantic Retrieval (Top-K chunks)
         ↓
   Prompt Engineering + Context Injection
         ↓
   LLM (Ollama/HuggingFace) → Response
         ↓
      Frontend Chat UI (with citations)
```

---

## 🛠️ Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Frontend     | React 18, Vite, Tailwind CSS, Framer Motion |
| Backend      | FastAPI, Python 3.10+               |
| LLM          | Ollama (llama3.2) or HuggingFace    |
| RAG          | LangChain + FAISS                   |
| Embeddings   | sentence-transformers (all-MiniLM-L6-v2) |
| Auth         | JWT (python-jose)                   |
| Storage      | SQLite (users, sessions, chat history) |
| Doc Parsing  | PyMuPDF, python-docx                |

---

## 📁 Project Structure

```
scholara/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── auth.py              # Auth endpoints
│   │   ├── chat.py              # Chat endpoints
│   │   ├── documents.py         # Upload endpoints
│   │   └── analytics.py        # Analytics endpoints
│   ├── core/
│   │   ├── config.py            # Config + settings
│   │   ├── database.py          # SQLite setup
│   │   └── security.py         # JWT + password hashing
│   ├── models/
│   │   ├── user.py              # User ORM model
│   │   ├── session.py           # Chat session model
│   │   └── document.py         # Document model
│   ├── services/
│   │   ├── rag_service.py       # RAG orchestration
│   │   ├── llm_service.py       # LLM wrapper
│   │   ├── embedding_service.py # Embedding + FAISS
│   │   └── document_service.py # Document ingestion
│   └── utils/
│       ├── chunker.py           # Text chunking
│       ├── parser.py            # PDF/DOCX/TXT parser
│       └── logger.py           # Logging setup
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/            # Chat UI components
│   │   │   ├── layout/          # Navbar, sidebar
│   │   │   ├── ui/              # Reusable UI primitives
│   │   │   ├── auth/            # Login/Signup forms
│   │   │   ├── upload/          # Document upload
│   │   │   └── analytics/      # Analytics widgets
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── Auth.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Chat.jsx
│   │   │   ├── Upload.jsx
│   │   │   └── Analytics.jsx
│   │   ├── hooks/               # Custom React hooks
│   │   ├── store/               # Zustand state
│   │   ├── lib/                 # API client, utils
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── rag_pipeline/
│   └── pipeline.py              # Standalone RAG demo
├── uploads/                     # Uploaded documents
├── vector_db/                   # FAISS index storage
├── .env.example
├── requirements.txt
├── setup.sh
└── README.md
```

---

## ⚡ Quick Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) (for local LLM)

### 1. Clone & Configure
```bash
git clone <your-repo-url>
cd scholara
cp .env.example .env
# Edit .env with your values
```

### 2. Install Ollama + Model
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2      # ~2GB — best free local LLM
# OR smaller model:
ollama pull phi3          # ~1.5GB
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
python main.py
# Backend runs at http://localhost:8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

### 5. Test the App
- Open http://localhost:5173
- Register an account
- Upload a research PDF
- Start chatting!

---

## 🔑 API Endpoints

| Method | Endpoint              | Description             |
|--------|-----------------------|-------------------------|
| POST   | /auth/register        | Create account          |
| POST   | /auth/login           | Get JWT token           |
| POST   | /documents/upload     | Upload document         |
| GET    | /documents/           | List documents          |
| POST   | /chat/message         | Send chat message       |
| GET    | /chat/history/{id}    | Get chat history        |
| GET    | /analytics/summary    | Get usage analytics     |

---

## 🧠 How RAG Works

1. **Ingestion**: Uploaded PDFs are parsed → text extracted
2. **Chunking**: Text split into 500-char chunks with 50-char overlap
3. **Embedding**: Each chunk → 384-dim vector via MiniLM
4. **Storage**: Vectors stored in FAISS index
5. **Retrieval**: Query embedded → cosine similarity search → top-5 chunks
6. **Generation**: Chunks + query injected into LLM prompt → answer with citations

---

## 🎯 Domain Specialization (Simulated Fine-tuning)

Since full fine-tuning is expensive, ScholARA uses:
- **System prompts**: Persona as academic research expert
- **Few-shot prompting**: Example Q&A in the prompt
- **Domain templates**: Specialized response formats for research
- **RAG grounding**: Answers always tied to uploaded papers

---

## 📊 Evaluation Metrics

- Retrieval Precision@K
- Answer relevance (BLEU/ROUGE approximation)
- Response latency
- User feedback scores

---

## 🚀 Future Scope

- Multi-modal (image/table extraction from PDFs)
- Cross-document reasoning
- LoRA fine-tuning on academic datasets
- Export citations in BibTeX format
- Collaborative research rooms

---

## 📋 Viva Questions & Answers

**Q: What is RAG?**
A: Retrieval-Augmented Generation — combining a retrieval system (vector search) with a generative LLM so answers are grounded in actual documents, reducing hallucinations.

**Q: Why FAISS over ChromaDB?**
A: FAISS is faster for pure similarity search with no persistence overhead; ChromaDB adds metadata filtering which we handle in SQLite.

**Q: How do you prevent hallucinations?**
A: By injecting retrieved chunks directly into the prompt and instructing the LLM to only answer from provided context. If no relevant chunk found, it says "not found."

**Q: What is sentence-transformers?**
A: A library for generating dense vector embeddings from text using pre-trained transformer models optimized for semantic similarity.

**Q: Why FastAPI over Flask?**
A: Async support, automatic OpenAPI docs, Pydantic validation, better performance.
