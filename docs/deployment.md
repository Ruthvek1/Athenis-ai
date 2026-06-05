# Athenis Production Deployment Guide

## Prerequisites
- Docker & Docker Compose
- Or a Kubernetes Cluster (EKS, GKE, AKS) with `kubectl`

## Option 1: Docker Compose (Single Node Production)
The easiest way to deploy Athenis is using the provided `docker-compose.prod.yml`. This provisions PostgreSQL with pgvector, Redis, the FastAPI backend, Celery workers, and the Next.js frontend.

1. Configure environment variables in `.env` (including `GEMINI_API_KEY`, `OPENAI_API_KEY`, `JWT_SECRET`).
2. Start the cluster:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
3. Run migrations on the backend container:
```bash
docker exec -it athenis-backend alembic upgrade head
```
4. Access the frontend at `http://your-server-ip:3000` and the API at `http://your-server-ip:8000`.

## Option 2: Kubernetes (Highly Available)
For enterprise workloads, use the provided `k8s/` manifests.

1. Build and push your images to a container registry:
```bash
docker build -t your-registry/athenis-backend:latest ./backend
docker build -t your-registry/athenis-frontend:latest ./frontend
docker push your-registry/athenis-backend:latest
docker push your-registry/athenis-frontend:latest
```

2. Create Secrets and ConfigMaps (Replace with real values):
```bash
kubectl create secret generic athenis-secrets \
  --from-literal=JWT_SECRET=super-secret \
  --from-literal=OPENAI_API_KEY=sk-xxxx \
  --from-literal=GEMINI_API_KEY=AIzaSy...

kubectl create configmap athenis-config \
  --from-literal=DATABASE_URL=postgresql+psycopg://user:pass@db:5432/athenis \
  --from-literal=REDIS_URL=redis://redis:6379/0
```

3. Deploy:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Continuous Integration (CI/CD)
The repository contains a GitHub Action (`.github/workflows/ci.yml`) that automatically lints, runs `pytest`, builds the Next.js frontend, and validates the Docker images on every push to `main`.
