import logging
from backend.core.database import SessionLocal
from backend.core.celery_app import celery_app
from backend.models.document import Document, DocumentChunk, DocumentStatus
from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService
from backend.core.observability import CELERY_TASK_LATENCY, DOCUMENT_CHUNKS_INDEXED
from sqlalchemy import func
import hashlib
import os
import time
import gc

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_document_task")
def process_document(self, document_id: int, file_path: str, file_type: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    start_time = time.time()
    db = SessionLocal()
    try:
        # Update celery state
        self.update_state(state='PROGRESS', meta={'status': 'Initializing'})
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found.")
            return

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Hash the file content
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Incremental indexing check
        if document.content_hash == content_hash and document.status == DocumentStatus.READY:
            logger.info(f"Document {document_id} content is unchanged. Skipping re-indexing.")
            return

        # 1. PROCESSING
        document.status = DocumentStatus.PROCESSING
        document.content_hash = content_hash
        db.commit()
        self.update_state(state='PROGRESS', meta={'status': 'Processing'})
        
        logger.info(f"Extracting text for document {document_id}")
        text = DocumentService.extract_text(file_bytes, file_type)
        
        # 2. CHUNKED
        document.status = DocumentStatus.CHUNKED
        db.commit()
        self.update_state(state='PROGRESS', meta={'status': 'Chunked'})
        
        logger.info(f"Chunking text for document {document_id}")
        chunks = DocumentService.chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        
        # 3. EMBEDDED (and INDEXED combined since pgvector handles both via save)
        document.status = DocumentStatus.EMBEDDED
        db.commit()
        self.update_state(state='PROGRESS', meta={'status': 'Embedding'})
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks of document {document_id}")
        
        # Batch requests to OpenAI/Gemini can handle multiple strings, but let's do it in manageable batches
        # Reduced to 5 to aggressively save memory on 512MB free tier hosting
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            
            # Simple retry loop for rate limits
            max_retries = 5
            embeddings = None
            for attempt in range(max_retries):
                try:
                    embeddings = EmbeddingService.get_embeddings(batch_chunks)
                    break
                except Exception as e:
                    if "429" in str(e) or "RateLimit" in str(e) or "Quota" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = 10 * (attempt + 1)
                            logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                            time.sleep(wait_time)
                        else:
                            raise e
                    else:
                        raise e
            
            if embeddings is None:
                raise Exception("Failed to generate embeddings after multiple retries.")
                
            for j, (chunk_text, embedding) in enumerate(zip(batch_chunks, embeddings)):
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i + j,
                    embedding=embedding,
                    fts_vector=func.to_tsvector('english', chunk_text)
                )
                db.add(doc_chunk)
            
            db.commit()
            
            
            # Sleep to respect Gemini's 100 requests per minute limit (which is ~1.6 req/sec)
            time.sleep(2)
            
            # Force garbage collection to prevent OOM kills on memory-constrained environments
            gc.collect()
            
        document.status = DocumentStatus.INDEXED
        db.commit()
        
        # 4. READY
        document.status = DocumentStatus.READY
        db.commit()
        
        # Record metrics
        DOCUMENT_CHUNKS_INDEXED.inc(len(chunks))
        
        logger.info(f"Document {document_id} successfully processed and ready.")
        
        return {"document_id": document_id, "status": "READY", "chunks": len(chunks)}
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.FAILED
            db.commit()
    finally:
        latency = time.time() - start_time
        CELERY_TASK_LATENCY.labels(task_name="process_document").observe(latency)
        
        # Invalidate document list cache so the UI sees the final status (READY or FAILED)
        from backend.core.cache import CacheService
        CacheService.delete("documents_list")
        
        # Clean up the temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")
                
        db.close()
