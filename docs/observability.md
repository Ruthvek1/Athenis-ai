# Athenis Observability & Monitoring

Athenis implements an enterprise-grade observability stack using **OpenTelemetry**, **Prometheus**, and **Grafana**. 
This allows us to track distributed systems metrics across the FastAPI backend, Celery workers, Postgres database, and external LLM APIs.

## Architecture
- **Metrics Exposure**: The FastAPI backend exposes a `/metrics` endpoint on port `8000` via the `prometheus-client` library.
- **Scraping**: A Dockerized Prometheus instance scrapes this endpoint every 15 seconds.
- **Visualization**: Grafana is connected to Prometheus via provisioning and auto-loads the `Athenis - Elite Dashboard`.

## Starting the Monitoring Stack
To start the observability infrastructure locally:
```bash
docker compose -f docker-compose.monitoring.yml up -d
```
- **Prometheus** will be available at `http://localhost:9090`
- **Grafana** will be available at `http://localhost:3001` (login: admin/admin)

## Key Metrics Tracked

### 1. HTTP API Metrics
- `fastapi_requests_total`: Tracks the total number of incoming HTTP requests, categorized by method and HTTP status code. Used to monitor the overall throughput and error rate (5xx).

### 2. RAG & LLM Metrics
- `rag_retrieval_latency_seconds`: A histogram tracking the exact execution time of the Hybrid Search (BM25 + pgvector) database queries. 
- `llm_generation_latency_seconds`: A histogram tracking the round-trip latency to external AI providers (e.g., OpenAI, Gemini) when generating embeddings or text.
- `llm_token_usage_total`: A counter tracking exact token spend separated by `token_type` (prompt vs. completion) and `model`. Essential for billing and cost auditing.

### 3. Background Tasks (Celery)
- `celery_task_latency_seconds`: Tracks the processing latency of Celery workers parsing and chunking documents.
- `document_chunks_indexed_total`: Tracks the total volume of text chunks embedded and saved to the vector database.

## Alerting
Prometheus is configured with `alert.rules.yml` which contains sample SLAs:
- **HighAPIErrorRate**: Triggers if >5% of requests fail over 5 minutes.
- **HighRetrievalLatency**: Triggers if the P95 retrieval latency exceeds 1s.
- **HighLLMLatency**: Triggers if the P95 LLM response exceeds 10s.
- **CeleryTasksPilingUp**: Triggers if Celery workers stall.
