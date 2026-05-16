"""
ScholARA — Chat API
POST /chat/sessions           - Create session
GET  /chat/sessions           - List sessions
GET  /chat/sessions/{id}      - Get session + messages
DELETE /chat/sessions/{id}    - Delete session
POST /chat/message            - Send message (non-streaming)
POST /chat/stream             - Send message (SSE streaming)
POST /chat/feedback           - Submit message feedback
"""

import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.session import ChatSession, ChatMessage
from backend.services.rag_service import get_rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Schemas ───────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str = "New Chat"
    document_ids: Optional[List[int]] = None


class ChatMessageRequest(BaseModel):
    session_id: int
    query: str
    document_ids: Optional[List[int]] = None


class FeedbackRequest(BaseModel):
    message_id: int
    feedback: str  # "positive" | "negative"


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[str]
    confidence: Optional[float]
    retrieved_chunks: int
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    title: str
    document_ids: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    data: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=data.title,
        document_ids=",".join(str(i) for i in data.document_ids) if data.document_ids else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chat sessions for the current user."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific session with all its messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    db.commit()


@router.post("/message")
async def send_message(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and get a RAG-powered response.
    Non-streaming — waits for full response.
    """
    # Verify session ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == data.session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rag = get_rag_service()
    result = await rag.process_query(
        db=db,
        session_id=data.session_id,
        user_id=current_user.id,
        query=data.query,
        document_ids=data.document_ids,
    )

    return {
        "content": result["content"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "retrieved_chunks": result["retrieved_chunks"],
    }


@router.post("/stream")
async def stream_message(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and stream the response via SSE.
    Frontend should use EventSource or fetch with ReadableStream.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == data.session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rag = get_rag_service()

    async def event_generator():
        async for token in rag.stream_query(
            db=db,
            session_id=data.session_id,
            user_id=current_user.id,
            query=data.query,
            document_ids=data.document_ids,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/feedback")
async def submit_feedback(
    data: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit thumbs up/down feedback for a message."""
    msg = db.query(ChatMessage).filter(ChatMessage.id == data.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if data.feedback not in ("positive", "negative"):
        raise HTTPException(status_code=400, detail="Feedback must be 'positive' or 'negative'")

    msg.feedback = data.feedback
    db.commit()
    return {"status": "ok"}
