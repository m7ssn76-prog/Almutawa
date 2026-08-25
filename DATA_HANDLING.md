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

### Provenance hash versioning

A SHA-256 value is not sufficient by itself to describe how an application record was fingerprinted. Knowledge-record provenance must therefore identify the hash construction version alongside the digest.

- Existing records that predate versioned hashing remain `legacy-v0`. Their historical hashes are not silently recalculated or relabeled.
- New records, and records deliberately updated through the governed API, use `canonical-json-v1`.
- `canonical-json-v1` hashes a deterministic JSON object containing the governed provenance fields plus the version marker itself, using stable key ordering and UTF-8 encoding before SHA-256.
- The API and AI evidence citations expose both `provenance_hash` and `provenance_version` so a verifier can select the correct reconstruction method.
- A migration or software update must not claim that a legacy digest was produced by a newer construction unless the record was actually reprocessed and the change is auditable.

These controls improve reproducibility and field-boundary integrity. They do not constitute a digital signature, trusted timestamp, PKI certificate, external notarization, or proof of institutional approval.

### Source precedence

When records conflict, use the strongest current evidence in this order unless an authorized policy states otherwise:

1. current authoritative source;
2. approved original source;
3. reproducible runtime or test evidence tied to a version or commit;
4. historical snapshot;
5. secondary summary.

A newer date alone is not enough to override a more authoritative source.

## OpenAI pre-pilot provider data boundary

The AI evidence-answer path is restricted to reviewed evidence that is both public in sensitivity and has a `synthetic` or `public` data origin. Internal, sensitive, restricted, and `approved_low_sensitivity` evidence is not eligible for this provider path.

Before a question can enter the provider path:

- the caller must explicitly classify the question as `public` or `synthetic` using the governed request boundary;
- missing or broader question classifications fail closed;
- the question must be supplied in the authenticated POST request body, not in a URL query parameter; GET question transport is intentionally unsupported to reduce exposure through URLs, access logs, browser history, proxies, and similar metadata surfaces;
- `ASA_OPENAI_PREPILOT_ENABLED=true` must be set for the controlled pre-pilot path;
- `ASA_OPENAI_DATA_TERMS_CONFIRMED=true` must be set only after the responsible operator has reviewed the applicable current provider data terms for the intended test;
- `ASA_AUDIT_HMAC_KEY` must be supplied through the approved environment/secret mechanism for new AI audit fingerprints and must not be committed to the repository;
- the runtime API credential must be supplied through the approved environment/secret mechanism and must not be committed to the repository.

The data-terms flag is an **operator confirmation gate only**. It is not Data Owner approval, Privacy/DPIA approval, InfoSec approval, contract-owner confirmation, enterprise authorization, or production approval.

The local AI audit does not intentionally store the raw question text. Historical pre-HMAC audit rows retain their prior `sha256-v0` semantics. New audit rows use a keyed `hmac-sha256-v1` question fingerprint plus the declared question data origin, event status, model identifier, and evidence IDs. The HMAC key is environment-backed and separate from the stored audit record. A keyed fingerprint reduces offline guessing risk compared with an unkeyed digest, but it is not encryption and must not be presented as irreversible anonymization.

New AI audit events are also linked through a versioned `hmac-sha256-chain-v1` integrity chain. Each chained event protects its previous event hash, question fingerprint metadata, declared data origin, status, model identifier, evidence IDs, and stored creation time. The chain key is derived from the environment-backed audit HMAC material using a separate domain, so the event-chain construction is cryptographically separated from the question-fingerprint construction. Existing records that predate chaining remain `legacy-unchained-v0`; they are not silently rewritten into a historical chain. The internal verifier checks the legacy-to-chain boundary, previous-hash links, and every chained event HMAC, allowing ordinary record edits or broken links to be detected during controlled verification.

This chain is **tamper-evident, not immutable**. A party with sufficient database access and the audit secret could potentially rebuild the chain, and the control is not an external timestamp, append-only institutional log, HSM-backed signature, SIEM/WORM store, or independent notarization. Those stronger guarantees remain external or future controls.

Provider-side processing, retention, access, residency, abuse-monitoring, and training-use conditions remain governed by the provider terms and the organization's authorized review; this repository must not infer or overstate those conditions.

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
- [ ] Provenance hashes identify the construction version and legacy hashes are not silently promoted.
- [ ] AI provider-path questions are explicitly classified public/synthetic, sent in the POST body rather than URL query parameters, and the provider data-terms gate is deliberately confirmed for the test.
- [ ] New AI audit fingerprints use the environment-backed keyed construction and do not persist the raw question text.
- [ ] New AI audit events form a verifiable keyed chain, while historical pre-chain records remain explicitly legacy.
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
