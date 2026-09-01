# GitFlow-like Branching

## Long-lived branches

| Branch | Role | Merge source | Release effect |
| --- | --- | --- | --- |
| `main` | Production governance releases | `release/*` and `hotfix/*` | Signed semantic-version tag |
| `develop` | Integrated next release | `feature/*`, `chore/*`, and reconciled release/hotfix changes | Candidate state |

`main` carries the active protected-delivery ruleset. `develop` is the lean
integration branch; ordinary review and the lightweight pull-request proof
support fast integration while release promotion receives the protected gate.

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
5. Create a signed `governance-v<semver>` tag on the merge commit.
6. Reproduce the tagged commit's `git archive --format=tar` SHA-256 digest.
7. Merge the tagged release forward into `develop`.
8. Remove the short-lived release branch after its forward merge is settled.
9. Create an evidence branch that records the tag object, accepted commit,
   archive digest, and reviewed proof locators in the promotion receipt.
10. Run `python3 tools/validate_governance.py --verify-release-coordinate` from
   the receipt-carrier commit, then merge the evidence branch into `develop`.
11. Publish schema digests and downstream upgrade guidance.

The signed tag identifies the accepted release subject. The later evidence
commit carries the observation and proves that the subject is its ancestor;
the receipt therefore expresses both roles while each commit carries only the
information available when it is created.

## Hotfix flow

1. Create `hotfix/<issue>-<slug>` from `main`.
2. Add the smallest complete repair with a regression test.
3. Merge through the protected `main` pull-request gate.
4. Tag the patch release.
5. Reconcile the released commit into `develop` and active release branches.

## Local proof and bounded hosted maintenance

The dependency-free validator and regression suite remain the complete
source-owned proof path. The repository has a monthly **100–300 runner-minute**
allocation for one small pull-request proof. Pull requests targeting `develop`
or `main` run the governance aggregate, language and secret-shape checks, and
repository regression suite on Python 3.13. One standard runner, read-only
permissions, cancellation of superseded runs, and a ten-minute ceiling keep
that observation bounded.

The manual `Governance` workflow retains advisory author feedback, language and
secret-shape passes, and the complete regression proof. A named receiver sets
`ENABLE_GITHUB_ACTIONS=true`, selects `confirm_run`, and dispatches it when the
wider evidence is material. The reusable workflows remain available to
reviewed callers through their bounded inputs.

Monthly dependency updates live in `.github/dependabot.yml`, target `develop`,
group minor and patch updates, and keep at most two update pull requests open.
Dependency pull requests use a distinct, bounded coordinate contract.
Admission requires three aligned facts:

- the complete source branch matches the configured Dependabot or Renovate
  grammar;
- the pull-request author is the corresponding GitHub bot identity;
- the target is `main` or `develop`.

The active configuration names GitHub Actions, so its admitted branch grammar
begins with `dependabot/github_actions/`. A future package ecosystem extends
the configuration, grammar, and regression fixtures in the same reviewed
change. Renovate uses its default `renovate/` branch prefix and hosted-app bot
identity. A self-hosted Renovate caller adds its exact app identity through a
reviewed policy change.

An activated security update may target the default branch. Its standing proof
is local validation plus human review, immutable action-reference inspection,
and the ordinary release evidence. An accepted change on `main` is reconciled
into `develop` so the next release retains the dependency repair. The
repository-local branch checker remains available to reviewers, and CODEOWNER
review continues to cover the dependency configuration and workflow contracts.

Setting `ENABLE_GITHUB_ACTIONS=false` rests the manual proof. Repository
settings can rest all hosted execution, and a reviewed return to
`.github/dependabot.manual.yml` rests dependency scheduling. The `main` ruleset
export preserves one approving review, CODEOWNER review, stale-review
dismissal, last-push approval, review-thread resolution, deletion,
non-fast-forward, and release-signature protection while its hosted
required-check set remains empty. A later hosted check becomes part of branch
policy only through a separate reviewed activation state with a stable context
and a funded execution path.

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
