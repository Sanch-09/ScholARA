"""
ScholARA — Text Chunker
Splits extracted text into overlapping chunks for embedding.
Uses character-based splitting with semantic section-awareness.
"""

import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from backend.core.config import settings


def detect_section(text: str) -> str:
    """Detect the likely section of a given text block based on common headers."""
    text_lower = text.lower()[:200]  # Check beginning of block
    sections = ["abstract", "introduction", "methodology", "methods", 
                "results", "discussion", "conclusion", "references", "background"]
    
    for sec in sections:
        if re.search(r'\b' + sec + r'\b', text_lower):
            return sec.capitalize()
    return "General"


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    document_id: int = None,
    filename: str = "",
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with metadata, preserving section context.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # Basic attempt to split by major sections first
    # This regex looks for common section headers
    section_pattern = re.compile(
        r'(?:\n|^)\s*(?:\d+\.?\s*)?(Abstract|Introduction|Methodology|Methods|Results|Discussion|Conclusion|References)\s*(?:\n|$)',
        re.IGNORECASE
    )
    
    # Split text roughly by sections
    parts = section_pattern.split(text)
    
    # parts will be: [text_before_first_match, Match1, text_after_match1, Match2, text_after_match2, ...]
    blocks = []
    if parts:
        blocks.append(("General", parts[0]))
        for i in range(1, len(parts), 2):
            if i+1 < len(parts):
                blocks.append((parts[i].capitalize(), parts[i+1]))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    chunks = []
    char_pos = 0

    for section_name, block_text in blocks:
        if not block_text.strip():
            continue
            
        raw_chunks = splitter.split_text(block_text)
        
        for i, chunk_content in enumerate(raw_chunks):
            # Prepend section context so the LLM and Embedder know where this comes from
            enriched_content = f"[Section: {section_name}]\n{chunk_content.strip()}"
            
            # Find approximate start position in original text
            start = text.find(chunk_content[:50], char_pos) if len(chunk_content) >= 50 else char_pos
            if start == -1:
                start = char_pos
            end = start + len(chunk_content)

            chunks.append({
                "content": enriched_content,
                "chunk_index": len(chunks),
                "document_id": document_id,
                "filename": filename,
                "section": section_name,
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
