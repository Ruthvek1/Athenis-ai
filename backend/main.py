from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, documents, chat, metrics, billing
from backend.core.logging_config import setup_logging
from backend.core.observability import setup_observability
from backend.core.database import engine

setup_logging()

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import structlog
import traceback
import os
from asgi_correlation_id import correlation_id

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operations with users and JWT authentication.",
    },
    {
        "name": "Documents",
        "description": "Upload, chunk, and index documents using background Celery workers.",
    },
    {
        "name": "Chat",
        "description": "AI conversational interface with context retrieval and streaming.",
    },
]

app = FastAPI(
    title="Athenis API (Elite)",
    description="Backend API for Athenis - Enterprise AI-Powered RAG Knowledge Assistant.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Athenis Engineering",
        "url": "http://github.com/athenis-rag",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# Setup OpenTelemetry
setup_observability(app=app, engine=engine)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    req_id = correlation_id.get() or "unknown"
    logger.error("Unhandled exception", exc_info=exc, request_id=req_id, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error.", "request_id": req_id}
    )

# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [url.strip() for url in frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID tracing
from asgi_correlation_id import CorrelationIdMiddleware
app.add_middleware(CorrelationIdMiddleware)

# API v1 prefix router
from fastapi import APIRouter
api_v1_router = APIRouter(prefix="/api/v1")

# Include routers into v1
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_v1_router.include_router(billing.router, prefix="/billing", tags=["Billing"])

app.include_router(api_v1_router)

# Mount metrics router outside of v1 since it's an infra endpoint
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/ready")
def readiness_check():
    # TODO: Add DB/Redis connectivity checks here in the future
    return {"status": "ready"}
