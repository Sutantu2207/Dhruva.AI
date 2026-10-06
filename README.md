# Dhruva.AI

> **Production-grade AI-powered career intelligence, adaptive learning, course delivery, student development, and institutional education platform for engineering students.**

---

## 🏛️ System Overview

Dhruva.AI is architected around a **deterministic-first hybrid model**:
- **Deterministic Application Engines**: Act as the authoritative source of truth for all assessments, skill-gap analysis, SM-2 spaced repetition scheduling, concept mastery graphs, and institutional analytics.
- **Controlled AI Orchestration**: Google Gemini is deployed strictly in an auxiliary, advisory, and tutoring capacity with mandatory PII sanitization and authorization scoping.
- **Enterprise RBAC**: Built for Students, Teachers, Mentors, HODs, Placement Officers, Institution Admins, and Platform Super Admins.

---

## 📦 Architecture Stack

| Tier | Technology |
|---|---|
| **Frontend** | Next.js 15+ (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide |
| **Backend** | FastAPI, Python 3.14, Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 16 + pgvector extension |
| **ORM / Migration** | SQLAlchemy 2.0 (asyncpg) + Alembic |
| **AI Orchestration** | Google Gemini (Scoped & PII-sanitized pipeline) |

For comprehensive architectural specifications and domain boundary documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🚀 Quickstart

### Prerequisites
- Node.js >= 20.x
- Python >= 3.11 (configured with Python 3.14)
- PostgreSQL 16 (or Docker Compose)

### 1. Database (Local Docker)
```bash
docker compose up -d postgres
```

### 2. Backend Setup
```bash
# In project root
backend\.venv\Scripts\Activate.ps1
backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
backend\.venv\Scripts\pytest backend/tests
backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000` and proxies API requests to `http://localhost:8000`.
