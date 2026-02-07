from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from backend.core.database import Base
from backend.core.config import settings
import enum

class DocumentStatus(str, enum.Enum):
    UPLOADED = "Uploaded"
    PROCESSING = "Processing"
    CHUNKED = "Chunked"
    EMBEDDED = "Embedded"
    INDEXED = "Indexed"
    READY = "Ready"
    FAILED = "Failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt, md
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    content_hash = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index('ix_document_chunks_fts', 'fts_vector', postgresql_using='gin'),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    
    # Vector column using pgvector
    embedding = Column(Vector(settings.VECTOR_DIMENSION))
    
    # Postgres Full-Text Search vector
    fts_vector = Column(TSVECTOR)
    
    document = relationship("Document", back_populates="chunks")
