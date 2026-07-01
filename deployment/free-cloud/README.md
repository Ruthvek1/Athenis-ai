# Athenis Free-Tier Cloud Deployment

This directory contains the configuration necessary to host the entire Athenis Enterprise RAG architecture (Next.js, FastAPI, Celery, PostgreSQL, Redis) completely for free. 

To achieve a $0 footprint while preserving the decoupled architecture, we combine the FastAPI API and the Celery background worker into a single Docker container managed by `supervisord`.

## Cloud Providers

1. **Database:** Create a free project on [Supabase](https://supabase.com/). They provide PostgreSQL 15+ with the `pgvector` extension natively installed.
2. **Redis:** Create a free serverless Redis database on [Upstash](https://upstash.com/).
3. **Backend Container:** Create a free Web Service on [Render](https://render.com/). Deploy using the `deployment/free-cloud/backend.Dockerfile`.
4. **Frontend:** Deploy the `frontend/` directory to [Vercel](https://vercel.com/) (Free).

## Required Environment Variables

### Backend (Render)
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[SUPABASE_ID].supabase.co:5432/postgres
REDIS_URL=rediss://default:[PASSWORD]@[UPSTASH_ENDPOINT]:[PORT]
LLM_API_KEY=your_gemini_or_openai_key
FRONTEND_URL=https://your-frontend.vercel.app
```

### Frontend (Vercel)
```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_DEMO_MODE=true
```

> **Demo Mode:** Setting `NEXT_PUBLIC_DEMO_MODE=true` transforms the application into a polished showcase. It hides the registration page, injects professional demo credentials (`admin@athenis.ai`), and provides an interactive onboarding checklist for first-time visitors to upload documents and begin chatting.
