# ASA/AOIP Knowledge Hub

A controlled software foundation for governed organizational knowledge management.

## Legal and ownership status

**Copyright © 2026 Abdulmohsen Basim Almutawa. All rights reserved.**

This project is proprietary and is not released under an open-source license. No permission is granted to copy, modify, publish, distribute, sublicense, sell, or deploy the source code or documentation without prior written authorization from the copyright owner.

This repository is an independent project. It is not an official product, system, endorsement, or publication of any employer, customer, government entity, or other organization.

## PUBLIC-SAFE REPOSITORY MODE

This repository is intentionally maintained as a **public-safe technical repository**. Public visibility is not permission to publish protected information and does not grant open-source rights.

Every committed byte must be treated as publicly accessible. The repository may contain only:

- synthetic test data;
- public information that is lawful to reuse;
- project-owned technical material cleared for public disclosure; or
- low-sensitivity material with explicit written approval for this exact public purpose.

Protected, confidential, restricted, operational, personal, customer, employer, supplier, or otherwise non-public material must **never** be committed here. Any protected development must occur in a separate private or institutionally approved environment with its own access controls and review.

Connected GitHub metadata verified on 25 August 2026 reports this repository as `public`. Repository visibility and copyright/licensing are separate controls: public visibility does not make this project open source.

## Confidentiality and data boundary

The repository must contain only material permitted by PUBLIC-SAFE REPOSITORY MODE.

The following are prohibited:

- employer or customer documents, procedures, drawings, specifications, exports, screenshots, or internal communications;
- confidential, restricted, proprietary, operational, personal, or sensitive data not explicitly cleared for public disclosure;
- internal URLs, tenant identifiers, system names, credentials, tokens, passwords, API keys, private keys, or connection strings;
- unapproved logos, trademarks, branding, or material that could imply organizational approval;
- production database files, logs, backups, recordings, or user uploads.

See [DATA_HANDLING.md](DATA_HANDLING.md), [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md), and [SECURITY.md](SECURITY.md).

## Evidence freshness rule

Dated records under `.asa/`, historical workflow results, prior connector capability notes, automation records, and earlier visibility statements are **historical evidence snapshots**. They must not be treated as the current runtime, repository, automation, permission, or deployment state without a new live verification.

Current-state claims must be tied to current GitHub metadata, the relevant commit SHA, and the corresponding current status/check evidence. A historical `success`, `active`, `public`, `private`, `read-only`, or similar state does not automatically remain true later.

Branch protection/rulesets are separate GitHub settings controls. CI checks complement them but do not substitute for them.

## Included in the current technical draft

- FastAPI REST API and OpenAPI documentation
- SQLite persistence for synthetic local testing only
- Knowledge-item CRUD operations
- Keyword search and lifecycle status filtering
- fail-closed environment-backed bearer authentication for `/api/v1/*`
- input validation, auditable data-origin metadata, and provenance hashing
- governed OpenAI Agents SDK evidence-answer path
- structured AI output with evidence-ID validation
- privacy-preserving AI audit events using keyed, versioned HMAC-SHA-256 question fingerprints instead of raw questions
- Docker and Docker Compose for local verification
- automated tests and GitHub Actions CI
- repository policy scanning for secrets and prohibited file types

The bearer-token gate is a **pre-pilot local control only**. It is not enterprise SSO, RBAC, MFA, identity federation, user lifecycle management, access certification, or institutional authorization.

## Governance engines and closure gates

The project governance model now defines four shared control layers in the existing `.asa/audit-policy.json` policy:

1. **Evidence Engine** — requires source identity, owner/authority, version or commit, approval state, sensitivity, data origin, freshness, integrity reference, scope, and evidence classification before a claim can be promoted.
2. **KPI Engine** — requires definition, formula, source, measurement period, baseline where required, threshold, owner, eligibility gate, actual value, and evidence reference before a metric may be called an official KPI.
3. **Risk Engine** — requires a structured risk statement, cause, impact, likelihood, control, residual risk, owner/authority, review date, evidence reference, and status.
4. **Audit Engine** — requires event identity, timestamp, actor class, action, object reference, before/after state or hash, evidence reference, outcome, and classification while minimizing protected or personal data.

These definitions may close design/control-model gaps. They do not themselves close external institutional gates.

### Gap Closure Engine

Every remaining gap is placed into one of four categories:

| Category | Meaning | What can close it |
| --- | --- | --- |
| Close Internally | Definition, schema, control, test criteria, or local implementation gap | Reproducible implementation/test evidence tied to the relevant version or commit |
| Collect Real Evidence | Requires actual measured evidence | Real workflow measurements, real users, independent reviewers, or independent security evidence as applicable |
| External Approval Ready | Project can prepare the package but cannot self-approve | Recorded decision from the authorized external function |
| Hard Gate | Status must not progress while missing | Required evidence **and/or** authorized decision, according to the gate |

### Human Sustainability & Relationship Preservation — Design / Governance Only

ASA/AOIP treats sustained human cost as a governance concern when evaluating high-pressure work, projects, or periods of concentrated ambition. The purpose is **not** to reduce ambition. The purpose is to avoid describing an outcome as complete success while ignoring a material, foreseeable cost to human sustainability, social connection, or important relationships.

This principle is currently **Design / Governance Only**. It is not a clinical feature, employee-monitoring system, family-monitoring system, productivity score, psychological assessment, or automated intervention.

#### Evidence boundary

Public research reviewed for this design indicates that work-family conflict is associated with adverse well-being and mental-health outcomes, while social connection is recognized as relevant to health and well-being. These sources support treating relationship and social-connection costs as a legitimate governance consideration, but they do **not** justify assuming causation for an individual person or inferring a person's private mental state.

Public references:

- Liu D, Ni Y, Ma TSW, Fan X, Zhan Y, et al. (2026). *Work-family conflict and mental health: A systematic review and meta-analysis*. PLOS Medicine 23(7): e1005162. DOI: https://doi.org/10.1371/journal.pmed.1005162
- World Health Organization (2025). *From loneliness to social connection: charting a path to healthier societies — Report of the WHO Commission on Social Connection*. ISBN 978-92-4-011236-0. https://www.who.int/publications/i/item/978240112360

#### Reasoning linkage: S pattern

The design can be reasoned through a bounded **S pattern**:

1. **Source** — capture the stated observation, evidence, or experience without promoting it to fact beyond its scope.
2. **Signal** — identify a possible pattern such as sustained work pressure, repeated postponement of important relationships, or persistent boundary erosion.
3. **Science** — compare the signal against reliable public research and explicitly record limitations.
4. **Score** — where measurement is appropriate, assess the project or process against defined governance indicators; do not score people, relationships, affection, loyalty, or mental state.
5. **Decision** — choose a proportionate project or planning response, such as adding a boundary, review point, communication commitment, or recovery period.

#### Reasoning linkage: Pizza pattern

The same concept can be layered through the project's **Pizza pattern**:

- **Foundation** — values, human dignity, important relationships, health, and the purpose of the work.
- **Protection** — minimum boundaries that a high-pressure objective should not silently consume.
- **Linkage** — communicate the temporary pressure, expected duration, and affected commitments to the relevant people rather than relying on indefinite absence.
- **Development** — pursue the project, ambition, learning, promotion, or innovation within the declared boundary.
- **Stress test** — check whether the arrangement still works during the actual peak-pressure period, not only in calm conditions.
- **Measurement** — use non-invasive process indicators such as whether review dates occurred, whether the declared high-pressure period exceeded its end date, and whether agreed protected commitments were repeatedly displaced.
- **Verification** — distinguish a temporary, communicated sacrifice from an open-ended pattern that has become the default.
- **Impact** — evaluate achievement together with sustainability rather than treating output alone as sufficient evidence of success.

#### Cost of Arrival Gate

Before a high-demand initiative is treated as a controlled temporary exception, the design proposes a **Cost of Arrival Gate** with the following fields:

- objective and expected benefit;
- expected high-pressure duration and explicit end date;
- human or relationship domains likely to be affected;
- minimum protected commitments that should remain intact;
- review cadence during the high-pressure period;
- criteria for extending, stopping, or reducing the exception;
- post-period recovery or reconnection action;
- evidence classification for every claimed outcome.

A temporary sacrifice should not become an indefinite operating model merely because a new target replaces the previous target.

#### Privacy and dignity guardrails

This principle must not be implemented in a way that:

- monitors private family communications;
- ranks or scores family members, friends, employees, or personal relationships;
- infers affection, loyalty, intent, psychological state, or diagnosis;
- creates automated punishment or employment consequences from personal-life data;
- requires disclosure of unnecessary personal or family information;
- converts a reflective planning aid into covert surveillance.

If implemented later, any data collection must pass the existing Evidence, Risk, Privacy, and Audit controls and use the minimum information necessary for the stated purpose.

#### Derived insight

The governance insight is: **achievement and human sustainability are separate dimensions**. A project can meet its technical target while still creating an unmeasured human cost. Therefore ASA/AOIP should keep these dimensions separate in evidence and reporting rather than collapsing both into a single success label.

A useful review question is: *If the current operating pattern continued for several years, would the resulting human and relationship condition still be consistent with the stated purpose and values of the work?* This is a reflective governance prompt, not an automated judgment.

### Current P-004 hard gates

The following must remain visibly open until independently evidenced:

- **Independent Human Review:** required total `50`; current verified total remains `0/50`. AI pre-review and automated mapping do not increment this counter.
- **Real workflow baseline:** not established by synthetic or closed-set internal runs.
- **Real-user validation/satisfaction:** requires actual users and a documented measurement method.
- **Approved P-004 corpus:** requires the authorized content/data owner and a source-by-source approved list outside this public repository unless explicitly cleared for public disclosure.
- **Independent vulnerability assessment / penetration testing:** required when dictated by the target environment, policy, or risk; local CI is not a substitute.

### External approval gates

The project may prepare evidence and decision packages for these functions but may not mark them approved without an authorized recorded decision:

- formal Business Owner or authorized sponsor;
- Data/Content Owner;
- Information Security;
- Privacy/DPIA;
- Records/retention where applicable;
- Enterprise Architecture;
- Legal/IP and AI/provider/vendor contractual terms.

**Production Deployment** and **Institutional GO** remain `Not Approved / Not Demonstrated` until all applicable hard gates are closed with the required independent evidence and authorized decision.

## Governed OpenAI evidence path

The optional `/api/v1/ai/evidence-answer` endpoint is fail-closed and is intended only for controlled pre-pilot testing.

Its evidence boundary is intentionally stricter than the normal knowledge API:

- only records with `status=reviewed` are eligible;
- only records with `sensitivity=public` are eligible for transmission to the model provider;
- only `data_origin=synthetic` or `data_origin=public` records are eligible; `approved_low_sensitivity` and `unverified_legacy` records remain excluded from this provider path;
- transformed records must be `verified_against_original`;
- provenance hashing binds the data-origin metadata as part of the evidence identity;
- approval references are not included in the model evidence packet;
- no eligible evidence means no provider call is made;
- model-generated evidence IDs are validated against the exact candidate set before a response is released;
- Agents SDK tracing is disabled for this path;
- model responses are requested with `store=False`;
- the local AI audit table stores a keyed `hmac-sha256-v1` question fingerprint, its construction version, declared question data origin, event status, model name, and evidence IDs — not the raw question or model answer.

The path requires all of the following at runtime before a provider call is permitted: an operational local capability gate, `ASA_OPENAI_PREPILOT_ENABLED=true`, `ASA_OPENAI_DATA_TERMS_CONFIRMED=true`, a valid `OPENAI_API_KEY`, and an environment-backed `ASA_AUDIT_HMAC_KEY` for the keyed audit fingerprint. Secrets must be supplied through the runtime environment or an approved secret manager. **Never commit an API key, bearer token, or audit HMAC key to this repository.**

This integration is an **Internal Test Only** capability. It does not establish approved enterprise AI-provider terms, company-data authorization, production deployment, institutional approval, Enterprise SSO/RBAC, KMS/HSM, or a completed independent security assessment.

## Run locally

The runtime capability gate is fail-closed. A direct local internal-test run must explicitly opt in to every gate stage that the local test has actually satisfied; missing gate variables keep `/health` blocked rather than inferring readiness.

Create a strong temporary local API token without committing it to the repository:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export ASA_API_BEARER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ASA_GATE_AVAILABLE=true ASA_GATE_ELIGIBLE=true ASA_GATE_AUTHORIZED=true ASA_GATE_CONNECTED=true ASA_GATE_EXECUTED=true ASA_GATE_TESTED=true ASA_GATE_EVIDENCED=true
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Calls to `/api/v1/*` must include `Authorization: Bearer <token>`. The unauthenticated `/health` endpoint remains available only for bounded local health checks and does not return stored knowledge content. These local flags and the bearer token describe only an explicitly prepared local internal-test context; they do not establish production readiness or institutional approval.

To test the OpenAI evidence path, configure the API key outside the repository and explicitly enable the pre-pilot AI gate for that runtime. Do not place the key in source files, commits, issue comments, logs, or public workflow configuration.

## Run with Docker

```bash
export ASA_API_BEARER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
```

Docker Compose refuses to start the API service when `ASA_API_BEARER_TOKEN` is not supplied. It declares the same capability-gate flags explicitly for local-only verification and binds the service to `127.0.0.1`.

## Test

```bash
python scripts/repo_policy_check.py
ruff check app tests scripts
PYTHONPATH=. pytest -q
```

The automated AI-path tests use a synthetic credential-shaped value and a mocked Agents SDK run. CI does not require or use a real OpenAI API key, and successful CI does not prove live provider connectivity.

## Main endpoints

- `GET /health` — bounded unauthenticated local health check
- `GET /api/v1/external/health` — authenticated and additionally fail-closed by external-connection controls
- `POST /api/v1/ai/evidence-answer` — authenticated, reviewed-public-evidence-only, explicitly gated pre-pilot AI path; question is supplied in a JSON body and `X-ASA-Question-Data-Origin: public|synthetic` is required; GET question transport is intentionally unsupported
- `POST /api/v1/knowledge` — authenticated
- `GET /api/v1/knowledge?q=term&status=reviewed` — authenticated
- `GET /api/v1/knowledge/{id}` — authenticated
- `PATCH /api/v1/knowledge/{id}` — authenticated
- `DELETE /api/v1/knowledge/{id}` — authenticated

## Project status

**Discovery / Pre-Pilot — Revise.** This code is not approved for production, enterprise integration, company data, operational decisions, safety decisions, quality release, or engineering acceptance.

The gap-closure control model is now documented in existing project governance files, but real-evidence and external-approval gates remain open until their required evidence or authorized decisions exist.

## License

See [LICENSE.md](LICENSE.md). No open-source rights are granted.
