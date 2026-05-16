"""
ScholARA — Documents API
POST /documents/upload
GET  /documents/
GET  /documents/{id}
DELETE /documents/{id}
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.core.config import settings
from backend.models.user import User
from backend.models.document import Document
from backend.services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


# ── Schemas ───────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: Optional[int]
    title: Optional[str]
    status: str
    chunk_count: int
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a research document (PDF, DOCX, TXT).
    Ingestion runs in the background (non-blocking).
    """
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read content
    content = await file.read()

    # Validate size
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    doc_svc = get_document_service()

    # Save to disk
    file_path, saved_name = doc_svc.save_uploaded_file(content, file.filename)

    # Create DB record
    doc = doc_svc.create_document_record(
        db=db,
        owner_id=current_user.id,
        filename=saved_name,
        original_filename=file.filename,
        file_type=ext.lstrip("."),
        file_size=len(content),
    )

    # Kick off ingestion in background (uses its own DB session)
    background_tasks.add_task(doc_svc.ingest_document, doc.id, file_path)

    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents uploaded by the current user."""
    doc_svc = get_document_service()
    return doc_svc.get_user_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its FAISS embeddings."""
    doc_svc = get_document_service()
    deleted = doc_svc.delete_document(db, document_id, current_user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
