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

**Current control limitation:** this GitHub repository is presently public. Until repository visibility is changed through an authorized GitHub settings control, this repository must be treated as a public surface and must contain synthetic/public/explicitly approved low-sensitivity material only. Application code and CI checks reduce disclosure risk but do not make a public repository private. Branch protection/rulesets are also GitHub settings controls; CI policy checks complement them but cannot substitute for them.

## Included in the current technical draft

- FastAPI REST API and OpenAPI documentation
- SQLite persistence for synthetic local testing only
- Knowledge-item CRUD operations
- Keyword search and lifecycle status filtering
- Input validation
- Docker and Docker Compose for local verification
- Automated tests and GitHub Actions CI
- Repository policy scanning for secrets and prohibited file types

## Run locally

The runtime capability gate is fail-closed. A direct local internal-test run must explicitly opt in to every gate stage that the local test has actually satisfied; missing gate variables keep `/health` blocked rather than inferring readiness.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export ASA_GATE_AVAILABLE=true ASA_GATE_ELIGIBLE=true ASA_GATE_AUTHORIZED=true ASA_GATE_CONNECTED=true ASA_GATE_EXECUTED=true ASA_GATE_TESTED=true ASA_GATE_EVIDENCED=true
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. These local gate flags describe only an explicitly prepared local internal-test context; they do not establish production readiness or institutional approval.

## Run with Docker

```bash
docker compose up --build
```

Docker Compose declares the same gate flags explicitly for local-only verification and binds the service to `127.0.0.1`.

## Test

```bash
python scripts/repo_policy_check.py
ruff check app tests scripts
PYTHONPATH=. pytest -q
```

## Main endpoints

- `GET /health`
- `POST /api/v1/knowledge`
- `GET /api/v1/knowledge?q=term&status=reviewed`
- `GET /api/v1/knowledge/{id}`
- `PATCH /api/v1/knowledge/{id}`
- `DELETE /api/v1/knowledge/{id}`

## Project status

**Discovery / Pre-Pilot — Revise.** This code is not approved for production, enterprise integration, company data, operational decisions, safety decisions, quality release, or engineering acceptance.

## License

See [LICENSE.md](LICENSE.md). No open-source rights are granted.
