# DataWeaver 🚀

> **A Lean, Declarative Excel Automation Engine for Modern Business**

Transform fragmented Excel workflows into structured, versionable, and scalable assets. DataWeaver replaces fragile VBA macros with a high-density, parametric Rule Engine built on FastAPI and Pandas.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A.svg?style=flat&logo=celery)](https://docs.celeryq.dev)

**English** | [Español](README.es.md)

---

## 💎 The Lean Advantage

Standard automation projects often suffer from "Complexity Bloat". DataWeaver is built on **Density Principles**:

- **Super-Skills**: Instead of 50 different tools, we use parametric rules (e.g., `aggregate` handles sum, mean, count).
- **Super-Params**: Global parameters like `target_sheet` allow any transformation to materialize results directly.
- **Lean Architecture**: Consolidated API and Logic layers for maximum developer velocity and minimal maintenance overhead.

---

## 🏗️ Architecture

### High-Density System Design

```mermaid
graph TD
    UI[React/Dashboard] -->|REST API| API[Consolidated API Layer]
    API --> DB[(PostgreSQL)]
    API -->|Dispatch| Worker[The Weaver: Generalist Orchestrator]
    Worker -->|Execute| Logic[Parametric Rule Engine]
    Logic -->|IO| Files[Excel Materializer]
```

### Clean Structure

| Layer | Path | Responsibility |
|-----------|-----------|---------|
| **Core** | `app/core/` | Auth, DB, Models & Schemas (The Backbone) |
| **Logic** | `app/engine/logic.py` | Consolidated Rules & Super-Skills |
| **Orchestrator** | `app/engine/engine.py` | Context Management & Step Execution |
| **Gateway** | `app/api/` | Modular REST Endpoints & Routers |
| **Workers** | `app/tasks/` | Async Celery Tasks with Retry Logic |
| **Migrations** | `alembic/` | Database Schema Migrations (Alembic) |

---

## 🚀 Quick Start

### Run with Docker (Recommended)

```bash
git clone https://github.com/Medalcode/DataWeaver.git
cd DataWeaver
cp .env.example .env
docker-compose up -d
```

Services include health checks and auto-restart on failure.

### Local Development

```bash
# 1. Install & Setup
pip install -r requirements.txt
cp .env.example .env

# 2. Start Infrastructure
docker-compose up -d postgres redis

# 3. Run Database Migrations
alembic upgrade head

# 4. Start Engines
uvicorn app.main:app --reload
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## 📖 Parametric Rule Engine

DataWeaver uses **Declarative Steps**. Every step can materialize its result by simply adding the `target_sheet` parameter.

### 1. `filter` (Transformation)
Filters the current working dataset.
- **Params**: `column`, `operator`, `value`
- **Materialization**: `target_sheet` (Optional)

### 2. `aggregate` (Super-Skill)
Powerful data summarization.
- **Params**: `group_by`, `field`, `op` (`sum`, `mean`, `count`, `max`, `min`)
- **Required**: `target_sheet`

### 3. `move` (Legacy)
Simple materialization wrapper for the current dataset.

---

## 🧪 Testing & Linting

We believe in bulletproof automation.

```bash
# Set path and run tests
$env:PYTHONPATH = "backend"
pytest -v

# Lint with ruff
ruff check backend/

# Type-check with mypy
mypy backend/

# Format code
ruff format backend/
```

CI automatically runs tests, ruff, and mypy on every push.

---

## 🤝 Contributing

We prioritize **Density over Fragmentation**. Before adding a new file, ask: *"Can this be a parameter in an existing skill?"*

1. Fork the repo.
2. Build your feature in `logic.py`.
3. Document it in `skills.md`.
4. Submit your PR.

---

**Built with ❤️ for those who want to automate without the legacy baggage.**
