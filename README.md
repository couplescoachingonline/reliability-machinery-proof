# Reliability machinery proof

This disposable repository tests the control path before any integration with the Alexito vault.

## Claim under test

A builder may propose a three-part package, but cannot accept or apply it. Independent checks bind evidence and approval to the exact Git revision. The approved revision alone may be applied.

## Package contract

Every package must contain:

- `packages/<name>/<name>.md` — human-readable contract;
- `packages/<name>/<name>.json` — machine-readable contract;
- `packages/<name>/<name>.py` — deterministic implementation.

The JSON contract declares all three files and their SHA-256 digests. The verifier rejects omissions, undeclared files, digest drift, invalid paths, and failed package self-tests.

## Authority boundaries

| Authority | Allowed | Forbidden |
|---|---|---|
| Alex | Review and approve the exact pull-request revision | Approval by editing repository files |
| Builder bot | Create a branch and pull request | Push to `main`, approve, merge, deploy, edit protected workflow/policy |
| GitHub Actions verifier | Check the candidate and publish evidence | Modify or approve the candidate |
| Apply environment | Apply the reviewed revision after approval | Apply a different or unverified revision |

The repository code can test package integrity. GitHub branch rules, identities, and environment protection must enforce the authority boundaries. These claims remain **UNVERIFIED** until the remote attack tests pass.

## Required repository settings

Protect `main` with:

1. pull requests required;
2. one approval required;
3. dismiss stale approvals when new commits arrive;
4. `verify` required before merge;
5. direct pushes restricted;
6. force pushes and deletion disabled;
7. administrators may not bypass;
8. `.github/workflows/**`, `policy/**`, and `CODEOWNERS` owned by Alex;
9. builder uses a separate GitHub App or bot identity with no approval, merge, administration, or environment-deployment authority.

Create an `apply` environment that requires Alex's review and prevents self-review where the selected GitHub plan supports those controls.

## Local verification

Run `python3 verifier.py`. It writes `evidence/verification.json` and `CONTROL-ROOM.md`. A local pass proves only deterministic package checks; it does not prove remote identity or protected-branch enforcement.

## Acceptance

The proof is accepted only after every item in `attack-tests.md` has a retained PASS result and one valid proposal completes the full protected path.
