from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func
import time
from backend.core.observability import RAG_RETRIEVAL_LATENCY
from backend.models.document import DocumentChunk, Document, DocumentStatus
from backend.services.embedding_service import EmbeddingService

class RetrievalService:
    @staticmethod
    def search_vector(db: Session, query: str, top_k: int = 20, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query_embedding = EmbeddingService.get_embedding(query)
        distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        
        stmt = select(DocumentChunk, Document, distance_col).join(Document).filter(Document.status == DocumentStatus.READY)
        if workspace_id:
            stmt = stmt.filter(Document.workspace_id == workspace_id)
            
        stmt = stmt.order_by(distance_col).limit(top_k)
        results = db.execute(stmt).all()
        
        chunks = []
        for chunk, doc, distance in results:
            chunks.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "filename": doc.filename,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "score": 1.0 - distance  # similarity
            })
        return chunks

    @staticmethod
    def search_keyword(db: Session, query: str, top_k: int = 20, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        tsquery = func.websearch_to_tsquery('english', query)
        rank_col = func.ts_rank(DocumentChunk.fts_vector, tsquery).label("rank")
        
        stmt = select(DocumentChunk, Document, rank_col).join(Document).filter(Document.status == DocumentStatus.READY)
        stmt = stmt.filter(DocumentChunk.fts_vector.op('@@')(tsquery))
        if workspace_id:
            stmt = stmt.filter(Document.workspace_id == workspace_id)
            
        stmt = stmt.order_by(rank_col.desc()).limit(top_k)
        results = db.execute(stmt).all()
        
        chunks = []
        for chunk, doc, rank in results:
            chunks.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "filename": doc.filename,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "score": rank
            })
        return chunks

    @staticmethod
    def search_similar_chunks(db: Session, query: str, top_k: int = 5, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Hybrid search combining Vector Search and BM25 (FTS) using Reciprocal Rank Fusion (RRF).
        """
        start_time = time.time()
        try:
            # Fetch top N from both retrievers
            fetch_k = max(top_k * 3, 20)
            vector_results = RetrievalService.search_vector(db, query, top_k=fetch_k, workspace_id=workspace_id)
            keyword_results = RetrievalService.search_keyword(db, query, top_k=fetch_k, workspace_id=workspace_id)
            
            # Reciprocal Rank Fusion
            rrf_k = 60
            fused_scores = {}
            chunk_map = {}
            
            # Process Vector Ranks
            for rank, item in enumerate(vector_results):
                cid = item["chunk_id"]
                if cid not in fused_scores:
                    fused_scores[cid] = 0.0
                    chunk_map[cid] = item
                fused_scores[cid] += 1.0 / (rrf_k + rank + 1)
                
            # Process Keyword Ranks
            for rank, item in enumerate(keyword_results):
                cid = item["chunk_id"]
                if cid not in fused_scores:
                    fused_scores[cid] = 0.0
                    chunk_map[cid] = item
                fused_scores[cid] += 1.0 / (rrf_k + rank + 1)
                
            # Sort by RRF score descending
            sorted_chunks = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Take top_k
            final_results = []
            for cid, rrf_score in sorted_chunks[:top_k]:
                item = chunk_map[cid]
                item["similarity_score"] = round(rrf_score, 4) # Overwrite with RRF score for citations
                final_results.append(item)
                
            return final_results
        finally:
            latency = time.time() - start_time
            ws_id = str(workspace_id) if workspace_id else "unknown"
            RAG_RETRIEVAL_LATENCY.labels(workspace_id=ws_id).observe(latency)
