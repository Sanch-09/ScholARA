"""
ScholARA — Text Chunker
Splits extracted text into overlapping chunks for embedding.
Uses character-based splitting with sentence-boundary awareness.
"""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from backend.core.config import settings


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    document_id: int = None,
    filename: str = "",
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with metadata.
    
    Returns a list of chunk dicts:
    {
        "content": str,
        "chunk_index": int,
        "document_id": int,
        "filename": str,
        "char_start": int,
        "char_end": int,
    }
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # RecursiveCharacterTextSplitter tries to split on paragraphs → sentences → words → chars
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)

    # Build enriched chunk objects
    chunks = []
    char_pos = 0
    for i, chunk_content in enumerate(raw_chunks):
        # Find approximate start position
        start = text.find(chunk_content[:50], char_pos) if len(chunk_content) >= 50 else char_pos
        if start == -1:
            start = char_pos
        end = start + len(chunk_content)

        chunks.append({
            "content": chunk_content.strip(),
            "chunk_index": i,
            "document_id": document_id,
            "filename": filename,
            "char_start": start,
            "char_end": end,
        })

        char_pos = max(0, end - chunk_overlap)

    logger.info(
        f"Chunked document '{filename}' → {len(chunks)} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )
    return chunks


def get_chunk_stats(chunks: List[Dict]) -> Dict:
    """Return statistics about chunks for debugging/display."""
    if not chunks:
        return {}
    lengths = [len(c["content"]) for c in chunks]
    return {
        "total_chunks": len(chunks),
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
    }
