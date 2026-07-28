# GitFlow-like Branching

## Long-lived branches

| Branch | Role | Merge source | Release effect |
| --- | --- | --- | --- |
| `main` | Production governance releases | `release/*` and `hotfix/*` | Signed semantic-version tag |
| `develop` | Integrated next release | `feature/*`, `chore/*`, and reconciled release/hotfix changes | Candidate state |

## Short-lived branches

- `feature/<issue>-<slug>` — governance capability or compatible schema addition
- `fix/<issue>-<slug>` — behavior repair destined for `develop`
- `chore/<issue>-<slug>` — maintenance with stable external behavior
- `release/<semver>` — stabilization from `develop`
- `hotfix/<issue>-<slug>` — urgent production repair from `main`
- `support/<major.minor>` — time-bounded maintenance for a supported line

Lowercase ASCII slugs keep branch coordinates portable. An issue or decision ID
connects each branch to intent.

## Standard feature flow

1. Branch from current `develop`.
2. Add or update schemas, examples, documentation, and tests together.
3. Open a draft pull request early.
4. Reach green validation and resolve review conversations.
5. Gain CODEOWNER approval.
6. Merge into `develop` using squash or merge according to repository policy.
7. Remove the short-lived branch after merge.

## Release flow

1. Create `release/<semver>` from `develop`.
2. Stabilize version metadata, changelog, migration notes, and examples.
3. Run the full validation suite and downstream contract rehearsal.
4. Merge the release into `main` through an approved pull request.
5. Create a signed `v<semver>` tag on the merge commit.
6. Merge the released state back into `develop`.
7. Publish schema digests and downstream upgrade guidance.

## Hotfix flow

1. Create `hotfix/<issue>-<slug>` from `main`.
2. Add the smallest complete repair with a regression test.
3. Merge through the protected `main` pull-request gate.
4. Tag the patch release.
5. Reconcile the released commit into `develop` and active release branches.

## Compatibility policy

- A major schema release can require document migration.
- A minor release adds backward-compatible capability.
- A patch release repairs validation, examples, or explanations while preserving
  accepted document behavior.
- Deprecations name their successor field, migration path, and final supported
  release.

## Commit and pull-request posture

Commits describe the achieved state in imperative form, such as
`Add environment-bound receipt contract`. Pull requests include:

- intent and material effect;
- contracts changed;
- example and test evidence;
- compatibility and invalidation analysis;
- security and privacy effect;
- planned release class.

