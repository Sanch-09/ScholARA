"""
ScholARA — Embedding Service
Generates vector embeddings using sentence-transformers
and manages the FAISS index for similarity search.
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
from loguru import logger

from backend.core.config import settings


class EmbeddingService:
    """
    Manages:
    1. Text → vector conversion (SentenceTransformer)
    2. FAISS index: add, search, persist
    3. Chunk metadata store (JSON sidecar)
    """

    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner Product (cosine after normalize)
        self.chunks_store: List[Dict] = []  # Parallel list to FAISS vectors
        self._load_model()
        self._load_or_create_index()

    def _load_model(self):
        """Load the sentence transformer model (downloads on first use)."""
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded ✓")

    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        index_path = settings.FAISS_INDEX_PATH + ".index"
        meta_path = settings.FAISS_INDEX_PATH + ".meta.json"

        if os.path.exists(index_path) and os.path.exists(meta_path):
            logger.info("Loading existing FAISS index...")
            self.index = faiss.read_index(index_path)
            with open(meta_path, "r") as f:
                self.chunks_store = json.load(f)
            logger.info(f"FAISS index loaded: {self.index.ntotal} vectors, {len(self.chunks_store)} chunks")
        else:
            logger.info("Creating new FAISS index (IndexFlatIP)...")
            self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
            self.chunks_store = []

    def _save_index(self):
        """Persist the FAISS index and metadata to disk."""
        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)
        index_path = settings.FAISS_INDEX_PATH + ".index"
        meta_path = settings.FAISS_INDEX_PATH + ".meta.json"

        faiss.write_index(self.index, index_path)
        with open(meta_path, "w") as f:
            json.dump(self.chunks_store, f)
        logger.debug(f"FAISS index saved: {self.index.ntotal} vectors")

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Convert a list of texts to normalized embedding vectors."""
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-normalize for cosine similarity via IP
        )
        return embeddings.astype(np.float32)

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Embed and add chunks to the FAISS index.
        Returns the number of vectors added.
        """
        if not chunks:
            return 0

        texts = [c["content"] for c in chunks]
        logger.info(f"Embedding {len(texts)} chunks...")

        embeddings = self.embed_texts(texts)
        start_id = len(self.chunks_store)

        # Add to FAISS
        self.index.add(embeddings)

        # Store metadata (without the raw content for memory efficiency — keep it)
        for i, chunk in enumerate(chunks):
            self.chunks_store.append({
                "faiss_id": start_id + i,
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename", ""),
                "chunk_index": chunk.get("chunk_index", i),
                "content": chunk["content"],
                "char_start": chunk.get("char_start", 0),
                "char_end": chunk.get("char_end", 0),
            })

        self._save_index()
        logger.info(f"Added {len(chunks)} chunks. Total vectors: {self.index.ntotal}")
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = None,
        document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic similarity search.
        
        Args:
            query: User's question
            top_k: Number of results to return
            document_ids: If provided, filter results to these documents only
        
        Returns:
            List of chunk dicts with similarity scores
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty — no documents ingested yet")
            return []

        top_k = top_k or settings.TOP_K_RETRIEVAL

        # Embed query
        query_vec = self.embed_texts([query])  # shape (1, dim)

        # Search — retrieve more if filtering
        search_k = top_k * 5 if document_ids else top_k
        scores, indices = self.index.search(query_vec, min(search_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks_store):
                continue

            chunk = self.chunks_store[idx].copy()
            chunk["similarity_score"] = float(score)

            # Apply document filter
            if document_ids and chunk.get("document_id") not in document_ids:
                continue

            results.append(chunk)

            if len(results) >= top_k:
                break

        logger.debug(f"Search returned {len(results)} results for: '{query[:60]}...'")
        return results

    def delete_document_chunks(self, document_id: int):
        """
        Remove all chunks belonging to a document.
        Note: FAISS IndexFlatIP doesn't support in-place deletion,
        so we rebuild the index without those chunks.
        """
        remaining = [c for c in self.chunks_store if c.get("document_id") != document_id]
        removed = len(self.chunks_store) - len(remaining)

        if removed == 0:
            return

        logger.info(f"Removing {removed} chunks for document_id={document_id}, rebuilding index...")

        # Rebuild index
        self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
        self.chunks_store = []

        if remaining:
            texts = [c["content"] for c in remaining]
            embeddings = self.embed_texts(texts)
            self.index.add(embeddings)
            self.chunks_store = remaining

        self._save_index()
        logger.info(f"Index rebuilt: {self.index.ntotal} vectors remaining")

    def get_stats(self) -> Dict:
        return {
            "total_vectors": self.index.ntotal,
            "total_chunks": len(self.chunks_store),
            "embedding_dim": settings.EMBEDDING_DIMENSION,
            "model": settings.EMBEDDING_MODEL,
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
