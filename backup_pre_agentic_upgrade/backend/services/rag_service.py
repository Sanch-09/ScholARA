"""
ScholARA — RAG Service
Orchestrates the full RAG pipeline:
Query → Embed → Retrieve → Prompt → Generate → Return with citations
"""

import json
from typing import List, Dict, Optional, Tuple, AsyncGenerator
from loguru import logger
from sqlalchemy.orm import Session

from backend.services.embedding_service import get_embedding_service
from backend.services.llm_service import get_llm_service
from backend.models.session import ChatSession, ChatMessage
from backend.core.config import settings


class RAGService:
    """
    Full RAG pipeline orchestrator.
    
    Pipeline:
    1. Receive user query
    2. Embed query → vector
    3. Search FAISS → top-K chunks
    4. Build prompt with context + history
    5. Call LLM
    6. Return response + source citations
    7. Save to chat history
    """

    async def process_query(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        query: str,
        document_ids: Optional[List[int]] = None,
    ) -> Dict:
        """
        Main entry point for a chat query.
        Returns: {content, sources, confidence, retrieved_chunks}
        """
        logger.info(f"RAG query: session={session_id}, query='{query[:80]}...'")

        # 1. Get chat history for memory
        history = self._get_chat_history(db, session_id)

        # 2. Retrieve relevant chunks
        embedding_svc = get_embedding_service()
        chunks = embedding_svc.search(
            query=query,
            top_k=settings.TOP_K_RETRIEVAL,
            document_ids=document_ids,
        )

        logger.info(f"Retrieved {len(chunks)} chunks for query")

        # 3. Compute confidence score
        confidence = self._compute_confidence(chunks)

        # 4. Build RAG prompt
        llm_svc = get_llm_service()
        messages = llm_svc.build_rag_prompt(
            query=query,
            context_chunks=chunks,
            chat_history=history,
        )

        # 5. Generate response
        response_text = await llm_svc.generate_response(messages)

        # 6. Format sources
        sources = self._format_sources(chunks)

        # 7. Save messages to DB
        self._save_message(db, session_id, "user", query)
        self._save_message(
            db, session_id, "assistant", response_text,
            sources=sources,
            confidence=confidence,
            retrieved_chunks=len(chunks),
        )

        # 8. Update session title if first message
        self._maybe_update_session_title(db, session_id, query)

        return {
            "content": response_text,
            "sources": sources,
            "confidence": confidence,
            "retrieved_chunks": len(chunks),
        }

    async def stream_query(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        query: str,
        document_ids: Optional[List[int]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming version of process_query."""
        history = self._get_chat_history(db, session_id)

        embedding_svc = get_embedding_service()
        chunks = embedding_svc.search(
            query=query,
            top_k=settings.TOP_K_RETRIEVAL,
            document_ids=document_ids,
        )

        confidence = self._compute_confidence(chunks)
        sources = self._format_sources(chunks)

        llm_svc = get_llm_service()
        messages = llm_svc.build_rag_prompt(query, chunks, history)

        # Save user message immediately
        self._save_message(db, session_id, "user", query)

        # Stream tokens
        full_response = ""
        async for token in llm_svc.stream_response(messages):
            full_response += token
            yield token

        # Save assistant message after streaming completes
        self._save_message(
            db, session_id, "assistant", full_response,
            sources=sources,
            confidence=confidence,
            retrieved_chunks=len(chunks),
        )

        self._maybe_update_session_title(db, session_id, query)

        # Send metadata as final SSE event
        yield f"\n\n[METADATA]{json.dumps({'sources': sources, 'confidence': confidence})}"

    def _get_chat_history(self, db: Session, session_id: int) -> List[Dict]:
        """Fetch recent messages for context window."""
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
            .all()
        )
        # Return in chronological order
        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

    def _compute_confidence(self, chunks: List[Dict]) -> float:
        """
        Simple confidence score based on:
        - Number of chunks retrieved
        - Average similarity scores
        """
        if not chunks:
            return 0.1  # Low confidence if no context found

        scores = [c.get("similarity_score", 0) for c in chunks]
        avg_score = sum(scores) / len(scores)

        # Normalize: similarity scores from normalized vectors are in [-1, 1]
        # Typical good values: 0.5-0.9
        confidence = min(1.0, max(0.0, (avg_score + 0.2) * 0.9))
        return round(confidence, 3)

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format retrieved chunks into citation objects."""
        seen = set()
        sources = []

        for chunk in chunks:
            source_key = f"{chunk['filename']}_{chunk['chunk_index']}"
            if source_key in seen:
                continue
            seen.add(source_key)

            sources.append({
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "similarity": round(chunk.get("similarity_score", 0), 3),
                "preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            })

        return sources

    def _save_message(
        self,
        db: Session,
        session_id: int,
        role: str,
        content: str,
        sources: Optional[List] = None,
        confidence: Optional[float] = None,
        retrieved_chunks: int = 0,
    ):
        """Persist a chat message to the database."""
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources=json.dumps(sources) if sources else None,
            confidence=confidence,
            retrieved_chunks=retrieved_chunks,
        )
        db.add(msg)
        db.commit()

    def _maybe_update_session_title(self, db: Session, session_id: int, query: str):
        """Auto-generate session title from first user message."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session and session.title == "New Chat":
            # Use first 50 chars of first query as title
            title = query[:50].rstrip() + ("..." if len(query) > 50 else "")
            session.title = title
            db.commit()


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
