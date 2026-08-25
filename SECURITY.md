# Security Policy

## Supported status

ASA/AOIP is currently **Discovery / Pre-Pilot — Revise**. No version is approved for production, enterprise integration, safety, quality release, engineering acceptance, or operational decision-making.

## Reporting a security or privacy concern

Do not disclose secrets, personal data, internal organizational information, or vulnerability details in a public issue, discussion, pull request comment, screenshot, or log.

Report concerns to the repository owner through a private written channel already agreed with the authorized collaborators. When organizational information may be affected, use the authorized information-security, privacy, records, legal/IP, or data-owner channel.

A report should contain only the minimum information needed to identify the affected version and location. Do not reproduce protected data unnecessarily.

## Immediate response rules

When a possible exposure is found:

1. stop deployment, publication, and further sharing;
2. restrict access to the affected repository, branch, artifact, or environment;
3. rotate credentials and revoke tokens through their authorized owner;
4. remove the affected material from the active branch;
5. review commit history, forks, pull requests, workflow logs, artifacts, releases, caches, mirrors, and deployment services;
6. notify the relevant authorized functions privately;
7. preserve a sanitized incident record and corrective-action evidence;
8. do not claim complete removal unless all relevant locations have been checked.

## Security boundaries

The controlled pre-pilot must use:

- synthetic or explicitly approved low-sensitivity data only;
- least-privilege access;
- no secrets committed to source control;
- no public deployment configuration;
- no autonomous actions or source-system writes;
- no production database, email, chat, file-share, ERP, quality, HSE, engineering, or operational-system connections;
- human verification of cited sources;
- a documented stop mechanism.

## Risk Engine minimum model

Every tracked security, privacy, data, integration, or governance risk should identify:

- Risk ID;
- risk statement;
- cause;
- impact;
- likelihood;
- current control or mitigation;
- residual risk;
- accountable owner or required authority;
- review date;
- evidence reference; and
- status.

A risk that depends on external approval, real-user evidence, independent review, independent vulnerability assessment, or penetration testing cannot be marked closed by local automated tests alone.

### Hard security gates

The following remain hard gates for any enterprise or production claim unless independent evidence and authorized decisions show otherwise:

- enterprise authentication and authorization, including appropriate SSO/RBAC/MFA or equivalent controls;
- approved key and secret management such as the institutionally selected KMS/HSM or equivalent;
- authorized hosting and network architecture;
- independent vulnerability assessment and penetration testing when required by policy or risk;
- information-security review/approval;
- approved data/content scope;
- privacy/DPIA and records controls where applicable;
- provider/vendor due diligence and contractual data-handling terms;
- production monitoring, incident response, backup/restore, resilience, and change-control requirements appropriate to the target environment.

Passing CI, Docker tests, localhost authentication tests, static checks, or synthetic workflow checks does not close these gates.

## Pre-pilot API authentication gate

All `/api/v1/*` routes require a bearer token supplied through `ASA_API_BEARER_TOKEN`. The token must be at least 32 characters and must be provided through the runtime environment or an approved secret mechanism; it must never be committed to source control.

The gate is fail-closed:

- if the token is absent or too short, protected API routes return HTTP 503;
- if the Authorization header is missing, protected API routes return HTTP 401;
- if the supplied token does not match, protected API routes return HTTP 401;
- token comparison uses constant-time comparison;
- `/health` remains unauthenticated only to support bounded local health checks and does not expose stored knowledge content.

This bearer-token control is an **Internal Test Only / pre-pilot safeguard**. It is not enterprise SSO, RBAC, MFA, identity federation, access certification, user lifecycle management, or institutional authorization. Those controls remain required before any production or enterprise use.

## Production external-connection guard

The code contains a fail-closed external connectivity path for future authorized deployment testing. Its existence is **not** production approval or evidence of a production deployment. The external health route is also protected by the pre-pilot API authentication gate.

The external connection path requires all of the following at runtime:

- `ASA_PRODUCTION_MODE=true`;
- `ASA_PRODUCTION_APPROVED=true`;
- `ASA_EXTERNAL_ENABLED=true`;
- an `ASA_EXTERNAL_URL` using HTTPS only;
- the target host explicitly present in `ASA_EXTERNAL_ALLOWED_HOSTS`;
- no username or password embedded in the URL;
- DNS resolution that does not return private, loopback, link-local, multicast, reserved, or unspecified addresses;
- an operational capability gate;
- a bounded connection timeout between 1 and 10 seconds;
- a maximum accepted external response size of 65,536 bytes;
- redirects blocked by the client.

Secrets and credentials must be provided only through an approved runtime secret manager or environment mechanism and must never be committed to the repository. A passing external probe demonstrates only that the configured endpoint was reachable under these controls; it does not establish institutional approval, data-owner approval, security certification, or production readiness.

## Evidence required to close a security gap

A security gap may be classified as locally closed only when the relevant control is implemented, its test is reproducible, and the evidence is tied to the tested version or commit. The evidence should identify what was tested, expected behavior, actual result, version/commit, and the evidence reference.

Examples of claims that may be locally verified include fail-closed API behavior, local-only bind behavior, container execution, dependency checks, and synthetic persistence tests. The classification must remain **Internal Test Only** unless a stronger authorized gate is independently satisfied.

Claims such as "enterprise ready", "secure for company data", "penetration tested", "approved by InfoSec", "production deployed", or "institutionally approved" require their corresponding independent evidence or authorized decision and must not be inferred from local success.

## Repository checks

The CI workflow runs `scripts/repo_policy_check.py` to detect prohibited file types and common secret or organizational-data indicators. A passing check reduces risk but does not prove that the repository is free of confidential, personal, proprietary, or regulated information.

## Third-party dependencies

Dependencies must be pinned, reviewed, and tested. A successful dependency installation, test run, or container build is not an approval for deployment. Provider, hosting, data residency, retention, training-use, and contractual controls require separate review before non-synthetic data is used.

## Gap-closure authority boundary

The project may internally prepare and test security controls, threat assumptions, risk records, evidence requirements, and approval packages. It may not self-approve the functions reserved for an authorized Business Owner, Data Owner, Information Security, Privacy/DPIA, Records, Enterprise Architecture, Legal/IP, provider/vendor authority, or production change authority.

If a required external gate is absent, the correct state is **External Approval Required**, **Evidence Required**, **Blocked**, or **Revise** as appropriate — not Passed.

## No warranty or certification

This security policy is a project control document. It is not a security certification, penetration-test result, compliance attestation, legal opinion, or organizational approval.
