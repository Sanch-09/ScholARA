"""
ScholARA — Reranker Service
Improves retrieval quality using a cross-encoder model to re-score chunks.
"""

from typing import List, Dict
from loguru import logger
from sentence_transformers import CrossEncoder

from backend.core.config import settings


class RerankService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
            self.model = CrossEncoder(settings.RERANKER_MODEL, max_length=512)
            logger.info("Reranker model loaded ✓")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None

    def rerank(self, query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Rerank a list of chunks based on a query using CrossEncoder.
        """
        if not chunks:
            return []
        
        if not self.model:
            logger.warning("Reranker model not available, falling back to original ordering")
            return chunks[:top_k]

        # Prepare pairs of (query, chunk_content)
        pairs = [[query, chunk["content"]] for chunk in chunks]
        
        # Get scores
        scores = self.model.predict(pairs)
        
        # Attach scores to chunks and sort
        for i, chunk in enumerate(chunks):
            chunk["reranker_score"] = float(scores[i])
            
        # Sort descending by score
        chunks.sort(key=lambda x: x["reranker_score"], reverse=True)
        
        return chunks[:top_k]


# Singleton
_rerank_service = None

def get_rerank_service() -> RerankService:
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service
