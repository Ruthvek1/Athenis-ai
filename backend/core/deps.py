from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.config import settings
from backend.models.user import User, APIKey
import hashlib
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db), 
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        db_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
        if db_key:
            user = db.query(User).filter(User.id == db_key.user_id).first()
            if user:
                return user
                
    if token:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=403, detail="Could not validate credentials")
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            return user
            
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
