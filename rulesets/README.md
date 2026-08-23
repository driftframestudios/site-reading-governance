# Ruleset Exports

These files are reviewable request bodies for the GitHub repository rulesets
API. They encode the GitFlow-like protections described in `BRANCHING.md`.

Before installation:

1. confirm each CODEOWNER resolves and has eligible repository review access;
2. run `python3 tools/validate_governance.py` and the focused local tests;
3. confirm the branch exports contain no `required_status_checks` rule, preserving
   the empty hosted-check resting state;
4. confirm signed-commit and tag policy with the organization;
5. install the `develop` ruleset after the branch exists;
6. review the repository's active aggregate rule view.

GitHub Actions rests disabled in repository settings at a **$0** budget. The
manual governance proof remains available through repository enablement,
`ENABLE_GITHUB_ACTIONS=true`, explicit `confirm_run`, and manual dispatch. The
two reusable workflows remain caller-owned `workflow_call` contracts with zero
current callers in the five-repository LIMS family.

The branch exports preserve one approving review, CODEOWNER review, stale-review
dismissal, last-push approval, review-thread resolution, deletion,
non-fast-forward, and applicable signature protections with an empty hosted
required-check set. A future required status context becomes a new reviewed
export only after its caller, stable context, budget, and recovery route are
established.

The release-tag export covers `v*`, `spec-v*`, `candidate-v*`,
`governance-v*`, `comparison-v*`, and `forecast-*` coordinates so every
constellation release family receives deletion, update, and signature controls.

Installation uses an authenticated administrative operation outside this
package. The JSON exports remain versioned so policy changes receive the same
review as schema changes.
