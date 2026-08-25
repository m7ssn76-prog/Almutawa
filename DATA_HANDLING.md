# Data Handling Policy

## Purpose

This policy prevents confidential, internal, personal, sensitive, or unauthorized organizational information from entering the ASA/AOIP source repository, build logs, tests, issues, pull requests, demonstrations, or deployments.

## Default rule

**Do not add organizational data unless there is explicit written approval for the exact source, purpose, environment, users, retention period, and access level.**

The default development dataset is synthetic.

## Allowed content

Only the following may be used:

1. Synthetic examples created specifically for testing.
2. Public information that is lawful to reuse and contains no restricted personal data.
3. Low-sensitivity material with written approval from the authorized owner for this exact pre-pilot purpose.

## Prohibited content

Do not commit, upload, paste, attach, quote, screenshot, log, or reproduce:

- internal procedures, work instructions, controlled specifications, drawings, reports, presentations, spreadsheets, exports, recordings, or screenshots;
- confidential, restricted, proprietary, operational, customer, supplier, or project information;
- employee records, names linked to performance, personal contact information, identifiers, health information, location history, or other personal data not strictly required and approved;
- credentials, passwords, API keys, tokens, certificates, private keys, connection strings, tenant IDs, cookies, session data, or authentication headers;
- internal hostnames, intranet links, SharePoint links, private repository URLs, system identifiers, or non-public architecture details;
- source-system database files, logs, backups, message exports, mailbox content, chat exports, or production telemetry;
- logos, trademarks, branding, or material that could imply authorization or endorsement;
- information classified by an employer, customer, government entity, contract, or law as non-public.

## Repository storage controls

The repository must not track:

- `.env` files or secret files;
- database files or backups;
- Office documents, PDFs, archives, recordings, or raw uploads;
- certificates and private keys;
- exported datasets or logs.

The `.gitignore` and automated repository-policy check enforce part of this rule. They do not replace human review.

## Evidence Registry admissibility gate

A source may support an asserted result only when the evidence record identifies, at minimum:

- Evidence ID;
- source title or stable identifier;
- source location;
- source owner, author, or controlling authority when known;
- version, commit, revision, or other freshness marker;
- approval state;
- sensitivity classification;
- data origin;
- capture or verification time;
- integrity reference such as SHA-256, commit SHA, workflow run, or equivalent reproducible identifier;
- scope of what the evidence actually proves; and
- evidence classification such as Verified, Internal Test Only, Unverified, Requires Original Source, or External Approval Required.

If a required field is unknown, the source must not be silently promoted to authoritative evidence. The claim remains limited to the strongest supported classification.

### Source precedence

When records conflict, use the strongest current evidence in this order unless an authorized policy states otherwise:

1. current authoritative source;
2. approved original source;
3. reproducible runtime or test evidence tied to a version or commit;
4. historical snapshot;
5. secondary summary.

A newer date alone is not enough to override a more authoritative source.

## P-004 data and review boundary

For P-004, the public repository remains synthetic/public-safe. A future approved corpus must be controlled outside this public repository unless the exact material is explicitly cleared for public disclosure.

The P-004 corpus approval package must identify each proposed source by title or identifier, Evidence ID, version, storage location, owner, approval state, sensitivity, and justification for inclusion.

AI pre-review, synthetic closed-set checks, automated source mapping, or automated citation mapping are internal measurement aids only. They do **not** count as independent human review and do not change the official independent-human-review counter.

## KPI data eligibility

A metric must not be presented as an official KPI unless its underlying data is eligible for that use. At minimum, the KPI record must define:

- KPI ID and name;
- definition and formula;
- data source;
- measurement period;
- baseline when required;
- target or decision threshold when applicable;
- accountable owner;
- eligibility gate;
- actual measured value; and
- evidence reference.

Synthetic or internal-test measurements must remain visibly separated from real-user, operational, or institutionally approved measurements.

## Before every commit or pull request

The contributor must verify:

- [ ] All examples are synthetic, public, or explicitly approved.
- [ ] No internal document text or screenshot has been copied.
- [ ] No company, customer, employee, supplier, or project data is present.
- [ ] No credentials, internal URLs, tenant identifiers, or connection strings are present.
- [ ] No unapproved logo, trademark, or endorsement language is present.
- [ ] Evidence claims identify their source, scope, version/freshness, and classification.
- [ ] Internal-test metrics are not presented as official KPIs.
- [ ] AI pre-review is not counted as independent human review.
- [ ] The repository-policy check passes.
- [ ] The change remains within Discovery / Pre-Pilot scope.

## If protected information is discovered

1. Stop sharing, building, or deploying the affected version.
2. Remove the content from the current branch and working copies.
3. Treat exposed credentials as compromised and rotate them through the authorized owner.
4. Notify the appropriate information-security, privacy, records, legal/IP, or data owner through an approved private channel.
5. Assess whether Git history, workflow logs, artifacts, forks, caches, releases, or external deployments contain copies.
6. Do not claim deletion is complete until each relevant storage location has been checked by the authorized administrator.
7. Record the incident, decision, limitations, and corrective action without reproducing the protected content.

## Retention

Synthetic development records may be retained only as needed for controlled testing and audit. Approved non-synthetic content must follow the written retention and deletion decision of its authorized owner.

Evidence and audit records should retain only the minimum information required for reproducibility, provenance, decision traceability, and authorized review. Secrets, protected source content, or unnecessary personal data must not be copied into evidence records merely for convenience.

## Authority boundary

This policy supports project control. It does not replace employer policies, contracts, privacy law, cybersecurity requirements, records obligations, or formal legal advice.

Local implementation of these controls may close design or Internal Test Only gaps. It cannot close Data Owner, Privacy/DPIA, Records, InfoSec, Enterprise Architecture, Legal/IP, provider-contract, or production-authorization gates that require an authorized external decision.
