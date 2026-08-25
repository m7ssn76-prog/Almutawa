# Publication and Disclosure Policy

## Default position

ASA/AOIP is a proprietary Discovery / Pre-Pilot project. This repository operates in **PUBLIC-SAFE REPOSITORY MODE**: the repository may remain public, but publication of protected information is denied by default.

Public visibility does not grant an open-source license and does not authorize disclosure of employer, customer, supplier, partner, personal, operational, restricted, or otherwise non-public material.

## Public-safe repository requirement

Everything committed to this repository must be safe to treat as publicly accessible.

Allowed material is limited to:

- synthetic examples created for testing;
- public information that is lawful to reuse;
- project-owned technical material cleared for public disclosure; and
- low-sensitivity material with explicit written approval for this exact public purpose.

Protected development must occur in a separate private or institutionally approved environment with appropriate access controls. Protected material must never be copied into this public repository merely because a branch, workflow, issue, pull request, artifact, or commit appears temporary.

Changing repository visibility does not alter copyright ownership, licensing, confidentiality obligations, or prior exposure history.

## Material that must never be published here

- employer, customer, supplier, partner, or government documents;
- controlled procedures, drawings, specifications, records, reports, internal presentations, or screenshots;
- credentials, tokens, secrets, keys, certificates, cookies, connection strings, or tenant identifiers;
- internal URLs, private repository links, source-system names, or non-public network and architecture details;
- personal, sensitive, confidential, restricted, proprietary, operational, or contract-protected information not explicitly cleared for public disclosure;
- unapproved logos, trademarks, branding, or statements suggesting endorsement;
- raw user prompts, uploads, logs, recordings, feedback, or production telemetry;
- results described as independent validation, official KPI, compliance, certification, or production readiness without the required evidence and authority.

## Material that may be published in this repository

Only sanitized material within PUBLIC-SAFE REPOSITORY MODE may be committed. It may include:

- generic project descriptions;
- synthetic examples;
- public information lawful to reuse;
- technical material owned by the project owner and cleared for disclosure;
- internal-test results clearly labeled with their environment, limitations, sample size, reviewer status, and non-production boundary.

## Required review before adding non-synthetic material

The publication decision must identify, when applicable:

1. the exact files, commit, screenshots, links, and results proposed for publication;
2. copyright and third-party rights review;
3. data and privacy review;
4. security and secret-scan result;
5. removal of organizational names, logos, internal references, and endorsement implications unless specifically authorized;
6. owner approval; and
7. when employment-related material or context is involved, the relevant authorized Legal/IP, Information Security, Privacy/Records, Communications, and data/content-owner decisions.

## Evidence and status freshness

Dated `.asa` records, historical CI results, prior automation states, connector-capability notes, and earlier repository-visibility statements are historical snapshots. They do not define the current state unless they are re-verified against current GitHub metadata and current execution evidence.

A current-state claim must identify the relevant repository state, commit SHA, status/check evidence, and verification date where applicable. Historical records must be preserved as history rather than silently reinterpreted as current operational truth.

## Public statements

Permitted statements must distinguish among:

- **Internal check:** produced by the project team in a controlled test;
- **Independent validation:** completed and signed by qualified independent reviewers;
- **Official KPI or approval:** issued by the authorized organization.

No internal check may be described as an independent validation, official KPI, certified result, production deployment, or organizational approval.

## Releases and deployments

- Public repository visibility does **not** authorize a public release, package, hosted service, or production deployment.
- No automatic public-cloud deployment configuration may be committed unless the separate deployment governance and security decision explicitly authorizes it.
- Deployment requires a separately approved environment, data-flow review, access model, security assessment, retention plan, incident process, and written decision.
- A successful build, container run, status check, or internal test does not authorize deployment.

## Revocation and incident handling

If protected material is published:

1. stop further sharing and deployments;
2. remove accessible copies where authorized;
3. rotate exposed credentials;
4. review repository history, forks, workflow logs, artifacts, releases, caches, mirrors, and deployment platforms;
5. notify the appropriate authorized functions through a private channel;
6. document what is confirmed removed and what may remain outside project control.

Changing a repository from public to private reduces future access but does not prove that earlier forks or local copies no longer exist.
