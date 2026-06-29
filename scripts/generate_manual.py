import os
import datetime

OUTPUT_FILE = "Athenis_Technical_Documentation.md"

def get_tree(startpath):
    tree = ""
    for root, dirs, files in os.walk(startpath):
        if 'node_modules' in dirs: dirs.remove('node_modules')
        if 'venv' in dirs: dirs.remove('venv')
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if '.next' in dirs: dirs.remove('.next')
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree += f"{subindent}{f}\n"
    return tree

def get_file_content(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def generate_docs():
    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    
    # 1. Cover Page & Meta
    content = f"""---
title: Athenis AI Platform - Technical Reference Manual
author: Prepared by Ruthvek Kannan
date: {date_str}
geometry: margin=1in
header-includes:
  - \\usepackage{{draftwatermark}}
  - \\SetWatermarkText{{Prepared by Ruthvek Kannan}}
  - \\SetWatermarkScale{{0.5}}
  - \\SetWatermarkColor[gray]{{0.9}}
  - \\usepackage{{fancyhdr}}
  - \\pagestyle{{fancy}}
  - \\fancyhead[L]{{Athenis AI Technical Documentation}}
  - \\fancyhead[R]{{\\leftmark}}
  - \\fancyfoot[C]{{\\thepage}}
  - \\fancyfoot[L]{{Prepared by Ruthvek Kannan}}
toc: true
toc-depth: 4
numbersections: true
---

# Executive Summary

**Athenis** is an enterprise-grade Retrieval-Augmented Generation (RAG) platform. It was architected to solve critical enterprise challenges around secure document processing, robust role-based access control (RBAC), multi-tenant cost tracking, and AI provider lock-in. 

This document serves as the **Definitive Technical Reference Manual**. It contains an exhaustive analysis of every component, file, database schema, AI workflow, API endpoint, deployment strategy, and background job within the repository. It is designed so that a senior software engineer can rebuild, debug, scale, or extend the entire project relying solely on this document.

# Project Overview & Architecture

## System Architecture

Athenis relies on a decoupled microservices-inspired monolith. The system consists of:
1. **Next.js Frontend**: A React-based interface utilizing Tailwind CSS, handling Chat (User) and Dashboard (Admin) interfaces.
2. **FastAPI Backend**: An asynchronous Python backend providing RESTful APIs.
3. **PostgreSQL (pgvector)**: Relational database that also stores 768-dimensional embeddings for semantic search.
4. **Redis**: In-memory data structure store used for API rate limiting and caching.
5. **Celery**: Distributed task queue for asynchronous document processing (extraction, chunking, embedding).
6. **OpenTelemetry / Prometheus / Grafana**: Full observability stack for tracing requests, tracking retrieval latency, and visualizing metrics.
7. **LiteLLM**: The AI provider abstraction layer, allowing dynamic routing between Gemini, OpenAI, Anthropic, and local models.

```mermaid
graph TD
    classDef client fill:#3b82f6,stroke:#1d4ed8,color:#fff
    classDef frontend fill:#10b981,stroke:#047857,color:#fff
    classDef backend fill:#f59e0b,stroke:#b45309,color:#fff
    classDef db fill:#6366f1,stroke:#4338ca,color:#fff
    classDef ai fill:#ec4899,stroke:#be185d,color:#fff
    classDef worker fill:#8b5cf6,stroke:#6d28d9,color:#fff

    U[User Client]:::client -->|HTTPS| N[Next.js Frontend]:::frontend
    A[Admin Client]:::client -->|HTTPS| N
    
    N -->|REST / JWT| API[FastAPI Backend]:::backend
    
    API -->|Read/Write| DB[(PostgreSQL + pgvector)]:::db
    API -->|Hybrid Search| DB
    API -->|Token Sync/Rate Limit| Redis[(Redis)]:::db
    
    API -->|LiteLLM| LLM[LLM Provider]:::ai
    
    API -->|Task| Celery[Celery Worker]:::worker
    Celery -->|Extract/Chunk| Celery
    Celery -->|Embed| LLM
    Celery -->|Save Vectors| DB
```

## AI System & RAG Pipeline

### Hybrid Search (Reciprocal Rank Fusion)
The RAG pipeline utilizes a highly advanced **Hybrid Search** algorithm. It does not rely solely on Vector Search.
1. **Vector Search (Cosine Similarity)**: Queries `pgvector` to find semantically similar chunks.
2. **Keyword Search (BM25 / FTS)**: Queries PostgreSQL Full-Text Search using `ts_rank` and `websearch_to_tsquery` to find exact keyword matches.
3. **Reciprocal Rank Fusion (RRF)**: A mathematical algorithm that merges the ranks from both searches. The formula applied is `1.0 / (k + rank)`.

### Provider Abstraction
The system uses `litellm` to abstract LLM calls. This prevents vendor lock-in. Currently configured to route `gemini-2.5-flash` natively.

## Security & RBAC
- **Authentication**: JWT-based (JSON Web Tokens). Passwords hashed using `bcrypt`.
- **Roles**: 
  - `User`: Can only access the `/chat` agent interface.
  - `Admin`: Can access the `/dashboard` (Grafana metrics) and `/admin` (Document Upload) interfaces.
- **Enforcement**: Role validation occurs via the `/api/v1/auth/me` endpoint.

# Installation & Deployment Guide

## Hardware Requirements
- **CPU**: 4+ Cores (AMD64 or ARM64)
- **RAM**: 8GB Minimum (16GB recommended for heavy Celery processing)
- **Storage**: 20GB+ SSD

## Software Requirements
- Docker v24+
- Docker Compose v2+
- Python 3.13 (for local development)
- Node.js 20+ (for local development)

## Production Deployment (Docker Compose)
The project utilizes multi-stage Docker builds.

1. Create a `.env` file containing `GEMINI_API_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.
2. Run the core stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
3. Run the monitoring stack:
   ```bash
   docker compose -f docker-compose.monitoring.yml up -d
   ```

## Kubernetes Deployment
Manifests are located in `k8s/`. Apply them using:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

# Repository Structure

```text
{get_tree('.')}
```

# Source Code Walkthrough & Implementation Details

"""
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Generated Phase 1 of {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_docs()
