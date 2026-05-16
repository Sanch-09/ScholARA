"""
ScholARA — Document Service
Handles document upload, parsing, chunking, and embedding ingestion.
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from backend.core.config import settings
from backend.models.document import Document
from backend.utils.parser import parse_document, get_document_metadata
from backend.utils.chunker import chunk_text, get_chunk_stats
from backend.services.embedding_service import get_embedding_service


class DocumentService:
    """Manages the full document lifecycle: upload → parse → chunk → embed → store."""

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_uploaded_file(
        self, file_content: bytes, original_filename: str
    ) -> tuple[str, str]:
        """
        Save raw file bytes to disk.
        Returns (saved_path, unique_filename)
        """
        ext = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(self.upload_dir, unique_name)

        with open(save_path, "wb") as f:
            f.write(file_content)

        logger.info(f"File saved: {save_path} ({len(file_content)} bytes)")
        return save_path, unique_name

    def create_document_record(
        self,
        db: Session,
        owner_id: int,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        title: Optional[str] = None,
    ) -> Document:
        """Create a Document record in the database."""
        doc = Document(
            owner_id=owner_id,
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size,
            title=title or Path(original_filename).stem,
            status="pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def ingest_document(self, document_id: int, file_path: str):
        """
        Full ingestion pipeline (runs in background task with its own DB session):
        1. Parse text from file
        2. Chunk text
        3. Generate embeddings
        4. Store in FAISS
        5. Update document status
        """
        # Create a fresh DB session for the background task
        from backend.core.database import SessionLocal

        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                raise ValueError(f"Document {document_id} not found")

            # Step 1: Update status
            doc.status = "processing"
            db.commit()

            logger.info(f"Ingesting document: {doc.original_filename} (id={document_id})")

            # Step 2: Parse text
            text = parse_document(file_path)
            if not text.strip():
                raise ValueError("Document appears to be empty or unreadable")

            # Step 3: Chunk
            chunks = chunk_text(
                text=text,
                document_id=document_id,
                filename=doc.original_filename,
            )

            stats = get_chunk_stats(chunks)
            logger.info(f"Chunking stats: {stats}")

            # Step 4: Embed + store in FAISS
            embedding_svc = get_embedding_service()
            count = embedding_svc.add_chunks(chunks)

            # Step 5: Update document record
            doc.status = "ready"
            doc.chunk_count = count
            doc.processed_at = datetime.utcnow()
            db.commit()

            logger.info(f"✓ Document {doc.original_filename} ingested: {count} chunks")
            return {"status": "ready", "chunks": count}

        except Exception as e:
            logger.error(f"Ingestion failed for document {document_id}: {e}")
            try:
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.status = "error"
                    doc.error_message = str(e)
                    db.commit()
            except Exception:
                pass
            raise
        finally:
            db.close()

    def delete_document(self, db: Session, document_id: int, owner_id: int) -> bool:
        """Delete document from DB, disk, and FAISS."""
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()

        if not doc:
            return False

        # Delete from FAISS
        try:
            embedding_svc = get_embedding_service()
            embedding_svc.delete_document_chunks(document_id)
        except Exception as e:
            logger.warning(f"FAISS delete warning: {e}")

        # Delete file from disk
        file_path = os.path.join(self.upload_dir, doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")

        # Delete from DB
        db.delete(doc)
        db.commit()
        logger.info(f"Document {document_id} deleted")
        return True

    def get_user_documents(self, db: Session, owner_id: int):
        """Get all documents for a user."""
        return db.query(Document).filter(Document.owner_id == owner_id).all()


# Singleton
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
