"""
ScholARA — Standalone RAG Pipeline Demo
Run this script to test the full RAG pipeline from the command line
without needing the full web app running.

Usage:
    cd scholara/
    python rag_pipeline/pipeline.py

Requirements:
    - Ollama running: ollama serve
    - Model pulled:   ollama pull llama3.2
    - Dependencies:   pip install -r requirements.txt
"""

import sys
import os
import asyncio

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from backend.utils.parser import parse_document
from backend.utils.chunker import chunk_text, get_chunk_stats
from backend.services.embedding_service import EmbeddingService
from backend.services.llm_service import LLMService


async def run_demo(file_path: str, query: str):
    """
    Full RAG pipeline demo:
    1. Parse document
    2. Chunk text
    3. Embed + store in FAISS
    4. Search
    5. Generate response with citations
    """
    print("\n" + "="*60)
    print("  ScholARA RAG Pipeline Demo")
    print("="*60)

    # ── Step 1: Parse ────────────────────────────────────────
    print(f"\n📄 [1/5] Parsing document: {file_path}")
    text = parse_document(file_path)
    print(f"   ✓ Extracted {len(text):,} characters")

    # ── Step 2: Chunk ────────────────────────────────────────
    print(f"\n✂️  [2/5] Chunking text...")
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50,
                        document_id=1, filename=os.path.basename(file_path))
    stats = get_chunk_stats(chunks)
    print(f"   ✓ {stats['total_chunks']} chunks | avg length: {stats['avg_length']} chars")

    # ── Step 3: Embed ────────────────────────────────────────
    print(f"\n🧠 [3/5] Generating embeddings (all-MiniLM-L6-v2)...")
    embed_svc = EmbeddingService()
    count = embed_svc.add_chunks(chunks)
    print(f"   ✓ {count} vectors stored in FAISS")

    # ── Step 4: Retrieve ─────────────────────────────────────
    print(f"\n🔍 [4/5] Semantic search for: '{query}'")
    results = embed_svc.search(query, top_k=3)
    print(f"   ✓ Retrieved {len(results)} chunks")
    for i, r in enumerate(results):
        print(f"\n   Chunk {i+1} (score: {r['similarity_score']:.3f})")
        print(f"   {r['content'][:200]}...")

    # ── Step 5: Generate ─────────────────────────────────────
    print(f"\n🤖 [5/5] Generating response with LLaMA...")
    llm = LLMService()
    messages = llm.build_rag_prompt(query=query, context_chunks=results)
    response = await llm.generate_response(messages)

    print("\n" + "="*60)
    print("  ANSWER")
    print("="*60)
    print(response)
    print("="*60)

    print("\n📚 Sources:")
    for r in results:
        print(f"  • {r['filename']} — chunk {r['chunk_index']+1} (similarity: {r['similarity_score']:.3f})")

    return response


def main():
    # Default demo: use a sample file from docs/ folder
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "sample_paper.txt"
    )

    # Command-line args
    file_path = sys.argv[1] if len(sys.argv) > 1 else sample_path
    query = sys.argv[2] if len(sys.argv) > 2 else "What is the main contribution of this research?"

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print(f"\nUsage: python pipeline.py <path_to_document> '<your_question>'")
        print(f"Example: python pipeline.py uploads/paper.pdf 'What methodology was used?'")
        sys.exit(1)

    asyncio.run(run_demo(file_path, query))


if __name__ == "__main__":
    main()
