# Ruleset Exports

These files are reviewable request bodies for the GitHub repository rulesets
API. They encode the GitFlow-like protections described in `BRANCHING.md`.

Before installation:

1. confirm each CODEOWNER resolves and has eligible repository review access;
2. run `python3 tools/validate_governance.py` and the focused local tests;
3. confirm the branch exports contain no `required_status_checks` rule, preserving
   the independently reviewed hosted-check posture;
4. confirm signed-commit and tag policy with the organization;
5. install the `main` promotion ruleset and release-tag ruleset;
6. confirm `develop` remains the lean integration branch;
7. review the repository's active aggregate rule view.

The repository's **100–300 monthly runner-minute** allocation supports one
small pull-request proof. The manual governance proof remains available through
`ENABLE_GITHUB_ACTIONS=true`, explicit `confirm_run`, and manual dispatch. The
two reusable workflows remain caller-owned `workflow_call` contracts.

The `main` export preserves one approving review, CODEOWNER review,
stale-review dismissal, last-push approval, review-thread resolution,
deletion, non-fast-forward, and signature protections. `develop` remains a
lean integration branch. Release and hotfix branches remain short-lived and
advance through the protected `main` promotion pull request.

The release-tag export covers `v*`, `spec-v*`, `candidate-v*`,
`governance-v*`, `comparison-v*`, and `forecast-*` coordinates so every
constellation release family receives deletion, update, and signature controls.

Installation uses an authenticated administrative operation outside this
package. The JSON exports remain versioned so policy changes receive the same
review as schema changes.
