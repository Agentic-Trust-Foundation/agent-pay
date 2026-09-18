# Private Repository Conformance Authentication

## Purpose

The V1 cross-repository conformance check compares the canonical Agent-Pay contract vectors with the copy maintained by the private `agentic-trust` repository.

Because `agentic-trust` is private, the checker must authenticate its GitHub API request. The credential is supplied only to GitHub Actions through the `ATF_REPO_TOKEN` repository secret.

## Required secret

Create a repository secret in **Agent-Pay**:

`Settings -> Secrets and variables -> Actions -> New repository secret`

- Name: `ATF_REPO_TOKEN`
- Value: a credential that can read the private `Agentic-Trust-Foundation/agentic-trust` repository.

For a fine-grained personal access token, grant only:

- Repository access: `agentic-trust`
- Repository permissions: **Contents: Read-only**

Do not put the token in source code, workflow YAML, documentation, or command-line arguments.

A GitHub App installation token with equivalent read-only access may also be used if the organization later adopts GitHub App based automation.

## CI behavior

The workflow passes the secret to:

`tools/check_cross_repo_conformance.py`

The checker calls the GitHub Contents API with:

- `Authorization: Bearer <token>`
- `Accept: application/vnd.github+json`
- `X-GitHub-Api-Version: 2022-11-28`

The token is never printed.

If the secret is missing or cannot read the private ATF repository, the cross-repository conformance step fails closed with a diagnostic message.

## Security boundary

The token is only used to read the canonical conformance vector. It is not used by the Agent-Pay application, reference implementation, payment provider adapters, or runtime services.

No ATF repository content is made public as a fallback.

## Private repository rollout

After the secret exists, verify the Agent-Pay conformance workflow on `main`. The expected final step is:

`cross-repository conformance OK: 7 vectors`

This keeps both repositories private while preserving the V1 cross-repository contract gate.
