# GitFlow-like Branching

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Released documentation and schemas |
| `develop` | Integrated next release |
| `feature/<issue>-<slug>` | Maintained capability or compatible schema addition |
| `fix/<issue>-<slug>` | Repair destined for `develop` |
| `release/<semver>` | Stabilization from `develop` |
| `hotfix/<issue>-<slug>` | Urgent repair from `main` |

## Feature and release flow

1. Branch from `develop`.
2. Change schemas, examples, documentation, and focused tests together.
3. Merge through a reviewed pull request after required checks pass.
4. Create `release/<semver>` from `develop` for release stabilization.
5. Merge the release through the protected `main` branch and reconcile it into `develop`.

GitHub Rulesets, protected branches, required checks, and CODEOWNERS implement
the repository policy. Dependabot branches pass through the same native controls
and focused validation as human-authored branches. The repository carries no
second branch-policy engine.

Schema releases follow semantic versioning: major for consumer-shaping changes,
minor for compatible additions, and patch for corrections.
