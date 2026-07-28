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
- `forecast/<year>-q<quarter>-r<revision>` — preregistered forecast candidate
- `evidence/<receipt>-<slug>` — redacted receipt-link and evidence-manifest change
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

## Automated maintenance flow

Automated dependency pull requests use a distinct, bounded coordinate contract.
Admission requires three aligned facts:

- the complete source branch matches the configured Dependabot or Renovate
  grammar;
- the pull-request author is the corresponding GitHub bot identity;
- the target is `main` or `develop`.

The current Dependabot configuration monitors GitHub Actions, so its admitted
branch grammar begins with `dependabot/github_actions/`. A future package
ecosystem extends the grammar and regression fixtures in the same reviewed
change that enables that ecosystem. Renovate uses its default `renovate/`
branch prefix and the hosted-app bot identity. A self-hosted Renovate caller
adds its exact app identity through a reviewed policy change.

GitHub security updates target the default branch. An accepted automation
change on `main` is reconciled into `develop` so that the next release retains
the dependency repair. Required checks, CODEOWNER review, immutable action
references, and release evidence continue to apply to automated maintenance.
Dependabot-triggered validation operates with a read-only GitHub token and
Dependabot-scoped secrets. A dedicated read-only `pull_request_target` gate
checks out the exact pull-request base commit into `.branch-policy-base` and
executes its checker. Head content remains in the ordinary `pull_request`
validation path, while the policy gate receives the head branch and author only
as quoted event data. Automated changes continue through the same substantive
tests and review gates as human-authored changes.

The gate begins governing later proposals after its reviewed workflow exists on
the default branch and its checker exists on each target base. The introducing
pull request uses the previously released branch controls; accepted changes are
merged forward so `main` and `develop` expose the same admission contract.

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
