## Scope

Describe the change and why it is required for the controlled Discovery / Pre-Pilot scope.

## Confidentiality and data checklist

- [ ] All test data is synthetic, public, or explicitly approved for this exact use.
- [ ] No employer, customer, supplier, partner, or government documents or screenshots are included.
- [ ] No confidential, restricted, proprietary, operational, personal, or sensitive data is included.
- [ ] No credentials, tokens, private keys, connection strings, internal URLs, tenant IDs, or system identifiers are included.
- [ ] No unapproved logos, trademarks, branding, or endorsement language is included.
- [ ] No Office documents, PDFs, archives, recordings, databases, logs, backups, or raw uploads are tracked.
- [ ] The repository policy check passes.

## Ownership and licensing checklist

- [ ] I have the right and written authorization required to contribute every added item.
- [ ] The change does not grant an open-source or public-use license.
- [ ] Third-party licenses and notices have been reviewed where applicable.
- [ ] The change complies with `LICENSE.md`, `DATA_HANDLING.md`, and `PUBLICATION_POLICY.md`.

## Technical verification

- [ ] `python scripts/repo_policy_check.py`
- [ ] `ruff check app tests scripts`
- [ ] `python -m compileall -q app tests scripts`
- [ ] `PYTHONPATH=. pytest -q`
- [ ] Container build completed, when relevant.

## Decision boundary

- [ ] This change does not claim production readiness, company approval, certification, independent validation, or an official KPI.
- [ ] This change does not authorize deployment, company-data ingestion, source-system access, autonomous actions, or safety/quality/engineering decisions.

## Reviewers and evidence

List required reviewers, exact commit, test results, known limitations, and any external approval still pending.
