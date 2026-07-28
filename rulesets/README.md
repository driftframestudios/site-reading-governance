# Ruleset Exports

These files are reviewable request bodies for the GitHub repository rulesets
API. They encode the GitFlow-like protections described in `BRANCHING.md`.

Before installation:

1. confirm the CODEOWNER team exists and has repository access;
2. run the validation workflow once and confirm the emitted check context;
3. update the required status-check context if GitHub renders a qualified name;
4. confirm signed-commit and tag policy with the organization;
5. install the `develop` ruleset after the branch exists;
6. review the repository's active aggregate rule view.

The release-tag export covers `v*`, `spec-v*`, `candidate-v*`,
`governance-v*`, `comparison-v*`, and `forecast-*` coordinates so every
constellation release family receives deletion, update, and signature controls.

Installation uses an authenticated administrative workflow outside this package.
The JSON exports remain versioned so policy changes receive the same review as
schema changes.
