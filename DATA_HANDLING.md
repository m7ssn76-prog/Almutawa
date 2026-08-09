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

## Before every commit or pull request

The contributor must verify:

- [ ] All examples are synthetic, public, or explicitly approved.
- [ ] No internal document text or screenshot has been copied.
- [ ] No company, customer, employee, supplier, or project data is present.
- [ ] No credentials, internal URLs, tenant identifiers, or connection strings are present.
- [ ] No unapproved logo, trademark, or endorsement language is present.
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

## Authority boundary

This policy supports project control. It does not replace employer policies, contracts, privacy law, cybersecurity requirements, records obligations, or formal legal advice.
