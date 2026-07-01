from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import get_db
from backend.core.deps import get_current_active_user, get_current_admin_user
from backend.core.cache import CacheService
from backend.models.user import User
from backend.models.document import Document, DocumentStatus
from backend.tasks.document_tasks import process_document
from backend.core.celery_app import celery_app
import os
import uuid

router = APIRouter()

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Only admins can upload documents
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ["pdf", "docx", "txt", "md"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    content = file.file.read()
    
    # Save file to temporary location for Celery to pick up
    upload_dir = "backend/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.{file_extension}"
    temp_filepath = os.path.join(upload_dir, temp_filename)
    
    with open(temp_filepath, "wb") as f:
        f.write(content)
    
    # Create DB entry
    db_doc = Document(
        filename=file.filename,
        file_type=file_extension,
        status=DocumentStatus.UPLOADED,
        uploaded_by=current_user.id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Enqueue background task
    task = process_document.delay(db_doc.id, temp_filepath, file_extension, chunk_size, chunk_overlap)
    
    # Invalidate document list cache
    CacheService.delete("documents_list")
    
    return {
        "message": "Document uploaded successfully and is being processed", 
        "document_id": db_doc.id,
        "task_id": task.id
    }

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str, current_user: User = Depends(get_current_admin_user)):
    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }

@router.get("/")
def get_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    cached_docs = CacheService.get("documents_list")
    if cached_docs:
        return cached_docs
        
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    results = [{"id": d.id, "filename": d.filename, "status": d.status.value, "created_at": d.created_at.isoformat() if d.created_at else None} for d in docs]
    
    # Cache for 5 minutes
    CacheService.set("documents_list", results, expire=300)
    
    return results

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    db.delete(doc)
    db.commit()
    
    # Invalidate document list cache
    CacheService.delete("documents_list")
    
    return {"message": "Document deleted successfully"}
