#!/usr/bin/env bash
# ============================================================
# ScholARA — Auto Setup Script (Linux / macOS)
# ============================================================
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "  ███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗  █████╗ "
echo "  ██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗██╔══██╗"
echo "  ███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝███████║"
echo "  ╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗██╔══██║"
echo "  ███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║██║  ██║"
echo "  ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}  AI Research Paper Assistant — Setup Script${NC}"
echo "  =============================================="
echo ""

# ── Check Python ──────────────────────────────────────────────
echo -e "${CYAN}[1/6] Checking Python version...${NC}"
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ Python not found. Install Python 3.10+ from https://python.org${NC}"
    exit 1
fi
PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PY_VERSION found${NC}"

# ── Check Node ────────────────────────────────────────────────
echo -e "${CYAN}[2/6] Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Install from https://nodejs.org (v18+)${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"

# ── Create .env ───────────────────────────────────────────────
echo -e "${CYAN}[3/6] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from .env.example${NC}"
    echo -e "${YELLOW}  ⚠ Edit .env to customize settings (SECRET_KEY, model, etc.)${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# ── Python virtual env + deps ─────────────────────────────────
echo -e "${CYAN}[4/6] Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Python packages installed${NC}"

# ── Node deps ─────────────────────────────────────────────────
echo -e "${CYAN}[5/6] Installing frontend dependencies...${NC}"
cd frontend
npm install --silent
cd ..
echo -e "${GREEN}✓ Node packages installed${NC}"

# ── Create directories ────────────────────────────────────────
echo -e "${CYAN}[6/6] Creating required directories...${NC}"
mkdir -p uploads vector_db logs
echo -e "${GREEN}✓ Directories ready${NC}"

# ── Ollama check ──────────────────────────────────────────────
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  LLM Setup (Required)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
    echo ""
    echo "  Pulling recommended model (llama3.2 ~2GB)..."
    ollama pull llama3.2 || echo -e "${YELLOW}  ⚠ Pull failed — run manually: ollama pull llama3.2${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not found!${NC}"
    echo ""
    echo "  Install Ollama from: https://ollama.ai"
    echo ""
    echo "  After installing, run:"
    echo "    ollama pull llama3.2   (recommended, ~2GB)"
    echo "    # OR smaller option:"
    echo "    ollama pull phi3       (~1.5GB)"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  To start ScholARA:"
echo ""
echo -e "  ${CYAN}Terminal 1 — Start Ollama:${NC}"
echo "    ollama serve"
echo ""
echo -e "  ${CYAN}Terminal 2 — Start Backend:${NC}"
echo "    source venv/bin/activate"
echo "    python -m backend.main"
echo "    # API docs: http://localhost:8000/docs"
echo ""
echo -e "  ${CYAN}Terminal 3 — Start Frontend:${NC}"
echo "    cd frontend && npm run dev"
echo "    # App: http://localhost:5173"
echo ""
echo "  Quick test RAG pipeline:"
echo "    python rag_pipeline/pipeline.py docs/sample_paper.txt 'What is the main contribution?'"
echo ""
