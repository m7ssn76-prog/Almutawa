# ASA/AOIP Knowledge Hub

A tested MVP for governed organizational knowledge management. This repository is not a production deployment and does not claim connection to TechnipFMC, Azure, Replit, company systems, devices, or external databases.

## Included

- FastAPI REST API and OpenAPI documentation
- SQLite persistence
- Knowledge-item CRUD operations
- Keyword search and lifecycle status filtering
- Input validation
- Docker and Docker Compose
- Automated tests and GitHub Actions CI

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Run with Docker

```bash
docker compose up --build
```

## Test

```bash
ruff check app tests
pytest -q
```

## Main endpoints

- `GET /health`
- `POST /api/v1/knowledge`
- `GET /api/v1/knowledge?q=term&status=reviewed`
- `GET /api/v1/knowledge/{id}`
- `PATCH /api/v1/knowledge/{id}`
- `DELETE /api/v1/knowledge/{id}`

## Project status

**Discovery / Pre-Pilot — Revise.** This MVP provides a verifiable software foundation. Authentication, role-based access control, PostgreSQL, audit trails, document ingestion, semantic retrieval, and deployment hardening remain future work.
