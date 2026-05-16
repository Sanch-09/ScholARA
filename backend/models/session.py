"""
ScholARA — Chat Session & Message Models
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Chat")
    document_ids = Column(String, nullable=True)  # comma-separated doc IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession id={self.id} title={self.title}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)

    # RAG metadata
    sources = Column(Text, nullable=True)       # JSON string of source citations
    confidence = Column(Float, nullable=True)   # AI confidence score 0-1
    retrieved_chunks = Column(Integer, default=0)

    # Feedback
    feedback = Column(String, nullable=True)    # positive | negative | null
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage id={self.id} role={self.role}>"
