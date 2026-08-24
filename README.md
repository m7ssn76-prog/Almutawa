# ASA/AOIP Knowledge Hub

A controlled software foundation for governed organizational knowledge management.

## Legal and ownership status

**Copyright © 2026 Abdulmohsen Basim Almutawa. All rights reserved.**

This project is proprietary and is not released under an open-source license. No permission is granted to copy, modify, publish, distribute, sublicense, sell, or deploy the source code or documentation without prior written authorization from the copyright owner.

This repository is an independent project. It is not an official product, system, endorsement, or publication of any employer, customer, government entity, or other organization.

## Confidentiality and data boundary

The repository must contain only:

- synthetic test data;
- public information that is lawful to reuse; or
- low-sensitivity material that has explicit written approval for this exact purpose.

The following are prohibited:

- employer or customer documents, procedures, drawings, specifications, exports, screenshots, or internal communications;
- confidential, restricted, proprietary, operational, personal, or sensitive data;
- internal URLs, tenant identifiers, system names, credentials, tokens, passwords, API keys, private keys, or connection strings;
- unapproved logos, trademarks, branding, or material that could imply organizational approval;
- production database files, logs, backups, recordings, or user uploads.

See [DATA_HANDLING.md](DATA_HANDLING.md), [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md), and [SECURITY.md](SECURITY.md).

## Publication rule

Protected development is intended to take place in a **private repository**. Public deployment, public demonstrations, source publication, or sharing with third parties is prohibited unless the owner completes a documented confidentiality, security, legal/IP, and data review.

## Included in the current technical draft

- FastAPI REST API and OpenAPI documentation
- SQLite persistence for synthetic local testing only
- Knowledge-item CRUD operations
- Keyword search and lifecycle status filtering
- fail-closed environment-backed bearer authentication for `/api/v1/*`
- input validation and provenance hashing
- Docker and Docker Compose for local verification
- automated tests and GitHub Actions CI
- repository policy scanning for secrets and prohibited file types

The bearer-token gate is a **pre-pilot local control only**. It is not enterprise SSO, RBAC, identity federation, user lifecycle management, or institutional authorization.

## Run locally

Create a strong temporary local token without committing it to the repository:

```bash
export ASA_API_BEARER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Calls to `/api/v1/*` must include `Authorization: Bearer <token>`. The unauthenticated `/health` endpoint remains available for local container health checks and returns only bounded service/gate status.

## Run with Docker

```bash
export ASA_API_BEARER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
```

Docker Compose refuses to start the API service when `ASA_API_BEARER_TOKEN` is not supplied.

## Test

```bash
python scripts/repo_policy_check.py
ruff check app tests scripts
PYTHONPATH=. pytest -q
```

## Main endpoints

- `GET /health` — bounded unauthenticated health check
- `GET /api/v1/external/health` — authenticated and additionally fail-closed by external-connection controls
- `POST /api/v1/knowledge` — authenticated
- `GET /api/v1/knowledge?q=term&status=reviewed` — authenticated
- `GET /api/v1/knowledge/{id}` — authenticated
- `PATCH /api/v1/knowledge/{id}` — authenticated
- `DELETE /api/v1/knowledge/{id}` — authenticated

## Project status

**Discovery / Pre-Pilot — Revise.** This code is not approved for production, enterprise integration, company data, operational decisions, safety decisions, quality release, or engineering acceptance.

## License

See [LICENSE.md](LICENSE.md). No open-source rights are granted.
