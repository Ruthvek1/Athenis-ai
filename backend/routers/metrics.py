from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

@router.get("/", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus metrics endpoint.
    Exposes metrics for API latency, LLM latency, Token usage, Celery queues, etc.
    """
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
