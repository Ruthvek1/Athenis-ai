from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from backend.core.database import get_db
from backend.core.deps import get_current_active_user
from backend.models.user import User
from backend.models.chat import ChatSession, ChatMessage, MessageFeedback
from backend.models.metrics import TokenUsage
from backend.models.workspace import Workspace
from backend.services.ai_service import AIService
from backend.services.retrieval_service import RetrievalService
from backend.services.billing_service import BillingService

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[int] = None
    workspace_id: Optional[int] = None

class FeedbackRequest(BaseModel):
    is_positive: int
    comments: Optional[str] = None

class Citation(BaseModel):
    id: int
    filename: str
    chunk_index: int
    similarity_score: float

class ChatResponse(BaseModel):
    session_id: int
    answer: str
    citations: List[Citation]

@router.post("/", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if request.session_id:
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat_session = ChatSession(user_id=current_user.id, title=request.query[:50])
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
    system_prompt = None
    if request.workspace_id:
        # Enforce quota before generating
        BillingService.verify_quota(db, request.workspace_id)
        
        workspace = db.query(Workspace).filter(Workspace.id == request.workspace_id).first()
        if workspace and workspace.system_prompt:
            system_prompt = workspace.system_prompt

    # 1. Retrieve relevant context using Vector Search
    context_chunks = RetrievalService.search_similar_chunks(db, request.query, workspace_id=request.workspace_id)
    
    # 2. Get Chat History
    history = db.query(ChatMessage).filter(ChatMessage.session_id == chat_session.id).order_by(ChatMessage.created_at).all()
    formatted_history = [{"role": msg.role, "content": msg.content} for msg in history]
    
    # 3. Save User Message
    user_msg = ChatMessage(session_id=chat_session.id, role="user", content=request.query)
    db.add(user_msg)
    
    # 4. Generate Response via LLM
    answer, citations, metrics = AIService.generate_response(
        request.query, context_chunks, formatted_history, system_prompt=system_prompt
    )
    
    # Save Metrics
    token_usage = TokenUsage(
        user_id=current_user.id,
        session_id=chat_session.id,
        model=metrics["model"],
        provider=metrics["provider"],
        prompt_tokens=metrics["prompt_tokens"],
        completion_tokens=metrics["completion_tokens"],
        total_tokens=metrics["total_tokens"],
        latency_ms=metrics["latency_ms"]
    )
    db.add(token_usage)
    
    # 5. Save AI Message
    ai_msg = ChatMessage(
        session_id=chat_session.id, 
        role="assistant", 
        content=answer,
        citations=json.dumps(citations)
    )
    db.add(ai_msg)
    db.commit()

    return ChatResponse(
        session_id=chat_session.id,
        answer=answer,
        citations=citations
    )

@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Setup session
    if request.session_id:
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat_session = ChatSession(user_id=current_user.id, title=request.query[:50])
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
    system_prompt = None
    if request.workspace_id:
        # Enforce quota before generating
        BillingService.verify_quota(db, request.workspace_id)
        
        workspace = db.query(Workspace).filter(Workspace.id == request.workspace_id).first()
        if workspace and workspace.system_prompt:
            system_prompt = workspace.system_prompt

    context_chunks = RetrievalService.search_similar_chunks(db, request.query, workspace_id=request.workspace_id)
    history = db.query(ChatMessage).filter(ChatMessage.session_id == chat_session.id).order_by(ChatMessage.created_at).all()
    formatted_history = [{"role": msg.role, "content": msg.content} for msg in history]
    
    user_msg = ChatMessage(session_id=chat_session.id, role="user", content=request.query)
    db.add(user_msg)
    db.commit()

    # Note: For real streaming with DB saves, we'd need a wrapper generator that yields
    # and then saves the final concatenated string to the DB.
    # For MVP purposes, this provides the raw stream.
    generator = AIService.generate_stream(
        request.query, context_chunks, formatted_history, system_prompt=system_prompt
    )
    
    return StreamingResponse(generator, media_type="text/event-stream")

@router.post("/messages/{message_id}/feedback")
def submit_feedback(
    message_id: int,
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    msg = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    # Ensure user owns the session
    session = db.query(ChatSession).filter(ChatSession.id == msg.session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=403, detail="Not authorized to provide feedback for this message")
        
    feedback = db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()
    if feedback:
        feedback.is_positive = request.is_positive
        feedback.comments = request.comments
    else:
        feedback = MessageFeedback(
            message_id=message_id,
            is_positive=request.is_positive,
            comments=request.comments
        )
        db.add(feedback)
        
    db.commit()
    return {"message": "Feedback submitted successfully"}

@router.get("/sessions")
def get_chat_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]
