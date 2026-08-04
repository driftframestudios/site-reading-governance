# Dependency Automation and GitFlow Review — 2026-07-28

## Outcome

All five repositories now express automated maintenance as a governed merge
flow. Admission requires three agreeing coordinates:

1. a complete, anchored branch grammar;
2. the exact pull-request author for that grammar;
3. `main` or `develop` as the target.

The policy treats automation as a validated flow rather than a prefix bypass.
Ordinary tests, review, and release evidence continue after branch admission.

## Triggering evidence

Two live `site-reading-governance` pull requests supplied the concrete failure
case:

- `dependabot/github_actions/actions/setup-python-7.0.0`
- `dependabot/github_actions/actions/checkout-7.0.1`

Both were authored by `dependabot[bot]` and targeted `main`. Earlier branch
validation recognized release and hotfix sources for `main`, so these complete
Dependabot coordinates failed. Dependabot also reported that configured
`dependencies` and `governance` labels were absent from the repository.

The initial prefix exception restored delivery, while any contributor could
select the same prefix. The settled policy binds branch grammar to the event's
pull-request author and target. Malformed paths, look-alike authors, partial
event coordinates, unconfigured ecosystems, and source-branch targets fail
closed.

## Repository assessment

| Repository | Earlier posture | Current posture | Primary future risk |
| --- | --- | --- | --- |
| `site-reading-governance` | GitFlow gate rejected automated maintenance; prefix exception admitted spoofable look-alikes | Anchored Dependabot and Renovate grammar, exact author, target binding, configuration parity, direct/reusable workflow parity | Governance and local copies can drift after independent edits |
| `lims-eln-enterprise-implementation` | Inline shell gate rejected automated maintenance and omitted documented `experiment/*` return flow | Local checker, local workflow, exact automation identities, configured-ecosystem test, and `experiment/* → develop` regression | Required-check configuration must select the new branch-policy job |
| `lims-eln-program-specification` | GitFlow guidance was advisory | Repository-specific `SPEC`/`RCP` grammar plus local tested workflow | Branch-protection installation remains an external repository setting |
| `lims-eln-simulated-final-state` | GitFlow guidance was advisory | Local tested workflow with simulation branch grammar | Local policy can diverge from the governance reference vectors |
| `lims-eln-comparative-evidence` | GitFlow guidance was advisory | Local tested workflow with comparator branch grammar | Oracle-policy changes deserve independent code-owner review |

Each Dependabot configuration currently admits only the `github-actions`
ecosystem, uses monthly cadence, groups minor and patch changes, and preserves
major changes as separate review coordinates. The grammar derives the same
`github_actions` ecosystem token and tests configuration parity.

## Deliberate policy choices

### Source-controlled callers

The `AutomationRule` table is the extension point. Source-controlled rules make
each added caller, branch grammar, exact identity, and target set reviewable.
Mutable environment configuration would widen admission outside the reviewed
repository change and is therefore reserved for a future signed policy-input
contract.

The hosted Renovate identity is `renovate[bot]`. A self-hosted Renovate
installation carries its own actor identity and requires an explicit rule,
fixtures, and review before admission.

### Default-branch security updates

GitHub opens Dependabot security updates against the default branch. A
`target-branch: develop` setting would redirect version updates while leaving
security updates on the default branch and separating related customization.
The current policy accepts both `main` and `develop`, then requires an accepted
default-branch correction to merge forward into `develop`.

Reference:
[Dependabot pull requests](https://docs.github.com/en/enterprise-cloud@latest/code-security/concepts/supply-chain-security/dependabot-pull-requests)
and
[Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference).

### Workflow authority

Each repository uses a dedicated branch-policy workflow with read-only contents
permission. Its `pull_request_target` trigger supplies event coordinates, while
the single checkout resolves `pull_request.base.sha` from the base repository
into a static repository-specific policy path and projects only the checker.
The workflow executes that checker from the bounded directory. Pull-request
head content remains confined to ordinary read-only `pull_request` validation
and enters the branch gate only as quoted head-ref and author data.

This separates policy authority from proposed checker changes. A pull request
can exercise its proposed checker and tests as candidate behavior, while the
branch-admission result continues to use the checker already reviewed on its
target base. Immutable action coordinates, disabled checkout credential
persistence, bounded job duration, and the absence of secret transfer preserve
the narrow execution surface.

Activation has one deliberate bootstrap boundary: GitHub requires the
`pull_request_target` workflow file to exist on the default branch before the
event can run. The pull request introducing this gate therefore uses the
previously released controls. After review, the workflow lands on the default
branch and is merged forward to `develop`; each policy revision becomes
authoritative for subsequent runs only after its checker reaches the relevant
target base. Existing open pull requests can be synchronized or reopened to
obtain the newly active status.

Reference:
[Dependabot on GitHub Actions](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-on-actions),
[events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
and the
[secure use reference](https://docs.github.com/en/actions/reference/security/secure-use).

## High-value follow-ups

1. After the workflow is active on the default branch and target bases, install
   the branch-policy job as a required check for `main` and `develop` in each
   repository ruleset, with GitHub Actions selected as the expected status
   source where available.
2. Enable required CODEOWNER review in repository rulesets for the explicit
   source-controlled patterns covering `.github/workflows/`,
   `.github/dependabot.yml`, each local branch checker, its regression tests,
   and the governance or program control surfaces. Fresh review of the latest
   push preserves policy integrity when a proposal changes validation policy.
3. Publish a versioned, data-only conformance vector from governance and run
   the same vector through every local checker. Local code remains independent
   for Dependabot execution, while semantic drift becomes observable.
4. Decide explicitly whether ordinary version updates should target `develop`.
   Preserve the separate default-branch security-update path and merge-forward
   receipt in either choice.
5. Validate configured labels, assignees, and reviewers against live
   repository metadata before adding those fields to Dependabot configuration.
6. Add each newly configured package ecosystem to the branch grammar in the
   same reviewed change. The configuration-parity regression then proves the
   admitted ecosystem set.
7. Evaluate a pinned dependency-review check when repositories gain package
   manifests or lockfiles. Keep automated merge outside the current regulated
   evidence path; human review and release evidence remain the governing
   completion route.

GitHub rulesets can layer required checks, pull-request review, signatures, and
other protections; the most restrictive applicable settings prevail.
Reference:
[About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
and
[Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
