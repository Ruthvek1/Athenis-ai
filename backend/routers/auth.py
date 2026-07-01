from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.core.deps import get_current_user, get_current_active_user
from backend.core.config import settings
from backend.models.user import User, APIKey
from backend.schemas.user import UserCreate, UserResponse, Token, APIKeyCreate, APIKeyResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import secrets
import hashlib

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=UserResponse)
@limiter.limit("10/minute")
def register_user(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    # If it's the first user, make them admin
    user_count = db.query(User).count()
    is_admin = True if user_count == 0 else user_in.is_admin

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # DEMO MODE FEATURE: Clear all old documents when the demo admin logs in
    if form_data.username == "admin@athenis.ai":
        from backend.models.document import Document
        from backend.core.cache import CacheService
        db.query(Document).delete()
        db.commit()
        CacheService.delete("documents_list")
        
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/api-keys", response_model=APIKeyResponse)
def create_api_key(
    request: Request,
    api_key_in: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Generate a secure random string for the API key
    raw_api_key = f"ath_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()
    
    db_api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        name=api_key_in.name
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    # Return the raw key once
    return {
        "id": db_api_key.id,
        "name": db_api_key.name,
        "is_active": db_api_key.is_active,
        "api_key": raw_api_key
    }

@router.get("/api-keys", response_model=list[APIKeyResponse])
def get_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return [{"id": k.id, "name": k.name, "is_active": k.is_active} for k in keys]

@router.delete("/api-keys/{key_id}")
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    return {"message": "API key deleted successfully"}
