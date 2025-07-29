# Athenis – AI-Powered RAG Knowledge Assistant

Athenis is a cloud-scale Retrieval-Augmented Generation (RAG) based AI assistant designed to ingest various document types (PDF, DOCX, TXT, MD) and provide contextually accurate answers to user queries with source citations and similarity scores.

This project is built using a modern, scalable, and provider-agnostic architecture suitable for FAANG-level engineering.

## Architecture

- **Frontend**: Next.js (TypeScript), Tailwind CSS, Framer Motion.
- **Backend**: FastAPI (Python), SQLAlchemy (ORM).
- **Database & Vector Store**: PostgreSQL with `pgvector` for combined relational and vector storage.
- **Caching**: Redis.
- **AI/ML**: OpenAI API (Embeddings & LLM) wrapped in abstract service layers.
- **Infrastructure**: Docker Compose (for PostgreSQL and Redis).

## Features

- **Document Processing**: Asynchronous background tasks to parse, chunk, embed, and index documents.
- **State Machine**: Tracks document processing status (Uploaded -> Processing -> Chunked -> Embedded -> Indexed -> Ready).
- **Vector Search**: Uses cosine distance to find relevant chunks.
- **Citations & Confidence**: Responses include verifiable source citations and similarity scores.
- **Provider-Agnostic**: Abstraction layers (`ai_service.py`, `embedding_service.py`) allow easy switching to local models (e.g., Llama, Ollama).

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API Key

### Infrastructure Setup

1. Copy the environment variables:
   ```bash
   cp .env.example backend/.env
   # Edit backend/.env and add your OPENAI_API_KEY
   ```
2. Start the database and cache using Docker:
   ```bash
   docker compose up -d
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the Celery Worker (for async document processing):
   ```bash
   PYTHONPATH=. celery -A backend.core.celery_app worker --loglevel=info
   ```
6. Start the FastAPI server (in a separate terminal):
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

## Usage

1. Open `http://localhost:3000` to access the application.
2. Register a new user and login.
3. Access the Admin Dashboard from the Chat sidebar to upload documents (PDF, DOCX, TXT).
4. Wait for the processing status to become `Ready`.
5. Return to the Chat interface and query the knowledge base!
