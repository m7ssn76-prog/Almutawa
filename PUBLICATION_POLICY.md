# Publication and Disclosure Policy

## Default position

ASA/AOIP is a proprietary Discovery / Pre-Pilot project. Publication is **denied by default**.

Source code, documentation, demonstrations, screenshots, datasets, test results, architecture diagrams, issue discussions, workflow logs, and deployment links must not be made public unless the required review is completed and the owner gives written authorization.

## Private-development requirement

Protected development is intended to occur in a private repository with access limited to named collaborators who require access for the approved task.

A public repository, public fork, public release, public package, public deployment, or publicly accessible demonstration is not an approved storage or operating environment for protected project material.

## Material that must never be published

- employer, customer, supplier, partner, or government documents;
- controlled procedures, drawings, specifications, records, reports, internal presentations, or screenshots;
- credentials, tokens, secrets, keys, certificates, cookies, connection strings, or tenant identifiers;
- internal URLs, private repository links, source-system names, or non-public network and architecture details;
- personal, sensitive, confidential, restricted, proprietary, operational, or contract-protected information;
- unapproved logos, trademarks, branding, or statements suggesting endorsement;
- raw user prompts, uploads, logs, recordings, feedback, or production telemetry;
- results described as independent validation, official KPI, compliance, certification, or production readiness without the required evidence and authority.

## Material that may be considered for publication

Only a sanitized package may be considered, and only after review. It must be limited to:

- generic project description;
- synthetic examples;
- public information lawful to reuse;
- technical material owned by the project owner and cleared for disclosure;
- results clearly labeled with their test environment, limitations, sample size, reviewer status, and non-production boundary.

## Required approval before publication

The publication record must identify:

1. exact files, commit, screenshots, links, and results proposed for publication;
2. copyright and third-party rights review;
3. data and privacy review;
4. security and secret-scan result;
5. removal of organizational names, logos, internal references, and endorsement implications unless specifically authorized;
6. owner approval;
7. when employment-related material or context is involved, the relevant authorized Legal/IP, Information Security, Privacy/Records, Communications, and data/content-owner decisions.

## Public statements

Permitted statements must distinguish among:

- **Internal check:** produced by the project team in a controlled test;
- **Independent validation:** completed and signed by qualified independent reviewers;
- **Official KPI or approval:** issued by the authorized organization.

No internal check may be described as an independent validation, official KPI, certified result, production deployment, or organizational approval.

## Releases and deployments

- No public release or package is authorized.
- No automatic public-cloud deployment configuration may be committed in the controlled pre-pilot branch.
- Deployment requires a separate approved environment, data-flow review, access model, security assessment, retention plan, incident process, and written decision.
- A successful build does not authorize deployment.

## Revocation and incident handling

If protected material is published:

1. stop further sharing and deployments;
2. remove accessible copies where authorized;
3. rotate exposed credentials;
4. review repository history, forks, workflow logs, artifacts, releases, caches, mirrors, and deployment platforms;
5. notify the appropriate authorized functions through a private channel;
6. document what is confirmed removed and what may remain outside project control.

Changing a repository from public to private reduces future access but does not prove that earlier forks or local copies no longer exist.
