from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
import os

from prometheus_client import Counter, Histogram, Gauge

# Prometheus Custom Metrics
RAG_RETRIEVAL_LATENCY = Histogram(
    'rag_retrieval_latency_seconds',
    'Time spent retrieving vectors from pgvector',
    ['workspace_id']
)

LLM_GENERATION_LATENCY = Histogram(
    'llm_generation_latency_seconds',
    'Time spent generating response from LLM',
    ['model']
)

LLM_TOKEN_USAGE = Counter(
    'llm_token_usage_total',
    'Total tokens used by LLM',
    ['model', 'token_type'] # token_type: prompt, completion, total
)

CELERY_TASK_LATENCY = Histogram(
    'celery_task_latency_seconds',
    'Time spent processing background tasks',
    ['task_name']
)

DOCUMENT_CHUNKS_INDEXED = Counter(
    'document_chunks_indexed_total',
    'Total number of document chunks indexed into vector DB'
)

def setup_observability(app=None, celery_app=None, engine=None):
    resource = Resource.create(attributes={
        "service.name": "athenis-backend",
        "service.version": "1.0.0"
    })

    # Tracer Setup
    tracer_provider = TracerProvider(resource=resource)
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
    
    # We only add the exporter if explicitly configured in production to avoid local grpc errors
    if os.getenv("ENABLE_OTLP_EXPORTER") == "true":
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        tracer_provider.add_span_processor(processor)
        
    trace.set_tracer_provider(tracer_provider)
    
    # Instrumentation
    if app:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    if engine:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=tracer_provider,
        )
    if celery_app:
        CeleryInstrumentor().instrument()
