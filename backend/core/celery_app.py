import ssl
from celery import Celery
from celery.signals import worker_process_init
from backend.core.config import settings
from backend.core.observability import setup_observability

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.tasks.document_tasks"]
)

# Optional configuration, see the application user guide.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Let tasks execute at least once in case of worker failure
    task_acks_late=True,
)

# When using rediss:// (TLS), Celery requires explicit SSL configuration.
# This is needed for cloud Redis providers like Upstash.
if settings.REDIS_URL.startswith("rediss://"):
    celery_app.conf.update(
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
    )

@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    setup_observability(celery_app=celery_app)
