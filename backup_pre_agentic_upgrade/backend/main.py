"""
ScholARA — FastAPI Application Entry Point
"""

import os
import sys
from contextlib import asynccontextmanager

# Make sure backend/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.core.config import settings
from backend.core.database import init_db
from backend.utils.logger import setup_logger
from backend.api import auth, chat, documents, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Startup
    setup_logger(debug=settings.DEBUG)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   LLM Provider: {settings.LLM_PROVIDER} ({settings._get_model() if hasattr(settings, '_get_model') else settings.OLLAMA_MODEL})")
    logger.info(f"   Embedding Model: {settings.EMBEDDING_MODEL}")

    # Initialize DB tables
    init_db()
    logger.info("✓ Database initialized")

    # Pre-load embedding model (downloads on first use)
    from backend.services.embedding_service import get_embedding_service
    get_embedding_service()
    logger.info("✓ Embedding service ready")

    # Check LLM health
    from backend.services.llm_service import get_llm_service
    llm = get_llm_service()
    health = await llm.check_health()
    if health["status"] == "ok":
        logger.info(f"✓ LLM ({settings.LLM_PROVIDER}) ready")
    elif health["status"] == "degraded":
        logger.warning(f"⚠ LLM ({settings.LLM_PROVIDER}) not available — using built-in extractive mode")
        logger.info("  → For AI-powered answers, install Ollama: https://ollama.ai")
        logger.info("  → Then run: ollama serve && ollama pull llama3.2")
    else:
        logger.warning(f"⚠ LLM not ready: {health.get('error')}")
        logger.warning("  → Run: ollama serve && ollama pull llama3.2")

    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)

    logger.info(f"✓ {settings.APP_NAME} is ready at http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    logger.info(f"  📖 API Docs: http://localhost:{settings.BACKEND_PORT}/docs")

    yield

    # Shutdown
    logger.info("Shutting down ScholARA...")


# ── Create App ─────────────────────────────────────────────────

app = FastAPI(
    title="ScholARA API",
    description="AI Research Paper Assistant — RAG-powered academic chatbot",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS ───────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(analytics.router)


# ── Health Check ───────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from backend.services.llm_service import get_llm_service
    from backend.services.embedding_service import get_embedding_service

    llm_health = await get_llm_service().check_health()
    vector_stats = get_embedding_service().get_stats()

    return {
        "status": "ok",
        "llm": llm_health,
        "vector_db": vector_stats,
    }


# ── Run Directly ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
