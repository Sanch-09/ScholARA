"""
ScholARA — Analytics API
GET /analytics/summary   - User's usage summary
GET /analytics/admin     - Admin panel stats (admin only)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.models.document import Document
from backend.models.session import ChatSession, ChatMessage
from backend.services.embedding_service import get_embedding_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics summary for the current user."""
    # Document stats
    total_docs = db.query(func.count(Document.id)).filter(
        Document.owner_id == current_user.id
    ).scalar()

    ready_docs = db.query(func.count(Document.id)).filter(
        Document.owner_id == current_user.id,
        Document.status == "ready",
    ).scalar()

    total_chunks = db.query(func.sum(Document.chunk_count)).filter(
        Document.owner_id == current_user.id,
        Document.status == "ready",
    ).scalar() or 0

    # Session stats
    total_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.user_id == current_user.id,
    ).scalar()

    # Message stats
    total_messages = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .scalar()
    )

    user_messages = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatMessage.role == "user")
        .scalar()
    )

    # Feedback stats
    positive = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(
            ChatSession.user_id == current_user.id,
            ChatMessage.feedback == "positive",
        )
        .scalar()
    )

    negative = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(
            ChatSession.user_id == current_user.id,
            ChatMessage.feedback == "negative",
        )
        .scalar()
    )

    # Avg confidence
    avg_conf = (
        db.query(func.avg(ChatMessage.confidence))
        .join(ChatSession)
        .filter(
            ChatSession.user_id == current_user.id,
            ChatMessage.role == "assistant",
            ChatMessage.confidence.isnot(None),
        )
        .scalar()
    )

    # Recent sessions (last 5)
    recent_sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
        .limit(5)
        .all()
    )

    # Vector DB stats
    embedding_svc = get_embedding_service()
    vector_stats = embedding_svc.get_stats()

    return {
        "documents": {
            "total": total_docs,
            "ready": ready_docs,
            "total_chunks": total_chunks,
        },
        "sessions": {
            "total": total_sessions,
        },
        "messages": {
            "total": total_messages,
            "queries": user_messages,
        },
        "feedback": {
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": (
                round(positive / (positive + negative) * 100, 1)
                if (positive + negative) > 0 else None
            ),
        },
        "avg_confidence": round(float(avg_conf), 3) if avg_conf else None,
        "recent_sessions": [
            {"id": s.id, "title": s.title, "updated_at": s.updated_at.isoformat()}
            for s in recent_sessions
        ],
        "vector_db": vector_stats,
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "member_since": current_user.created_at.isoformat(),
        },
    }
