"""
ScholARA — Document Model
Represents an uploaded research paper
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf | docx | txt
    file_size_bytes = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Processing state
    status = Column(String, default="pending")  # pending | processing | ready | error
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Vector DB reference
    faiss_index_id = Column(String, nullable=True)  # namespace/key in FAISS

    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document id={self.id} filename={self.original_filename} status={self.status}>"
