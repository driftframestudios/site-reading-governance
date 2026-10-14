# Ruleset exports

## Purpose

This directory provides reviewable request bodies for GitHub repository
rulesets that implement the branch and tag protections described in
[`../BRANCHING.md`](../BRANCHING.md).

## Authority

[`main.json`](main.json) and [`release-tags.json`](release-tags.json) are
versioned policy proposals. The installed aggregate ruleset view in GitHub owns
hosted enforcement, and an authenticated repository administrator owns
installation. Local validation establishes export structure and agreement with
the checked-in branching contract.

## Use

- [`main.json`](main.json) preserves one approving review, CODEOWNER review,
  stale-review dismissal, last-push approval, review-thread resolution,
  deletion protection, non-fast-forward protection, and signature protection
  for the `main` release line.
- [`release-tags.json`](release-tags.json) covers `v*`, `spec-v*`,
  `candidate-v*`, `governance-v*`, `comparison-v*`, and `forecast-*` release
  coordinates with deletion, update, and signature controls.

The exports keep hosted required-status checks empty. Local proof and reviewed
hosted observations remain distinct evidence paths. `develop` continues as the
lean integration branch, while release and hotfix branches advance through the
protected `main` pull request.

Before installation:

1. confirm each CODEOWNER resolves and has eligible repository review access;
2. run the local proof below;
3. confirm the branch exports retain the intended hosted-check posture;
4. confirm signed-commit and tag policy with the repository owner;
5. install the `main` promotion and release-tag rulesets through authenticated
   administration; and
6. inspect the active aggregate rule view after installation.

The repository's 100–300 monthly runner-minute allocation supports one small
pull-request proof. The manual Governance proof remains available through
`ENABLE_GITHUB_ACTIONS=true`, explicit `confirm_run`, and manual dispatch. The
two reusable workflows remain caller-owned `workflow_call` contracts.

## Verify

From the repository root, run:

```bash
python3 tools/validate_governance.py
python3 -m unittest \
  tests.test_governance.GovernancePackageTests.test_ruleset_exports_preserve_governed_flow \
  tests.test_governance.GovernancePackageTests.test_main_promotion_ruleset_preserves_one_review_bundle \
  -v
```

These checks establish checked-in structure, branch and tag coverage, review
parameters, and agreement with the local branching contract. GitHub's active
rules and their practical enforcement become established through the
post-install aggregate view and a fitting protected-delivery observation.

## Next route

- Read [`../BRANCHING.md`](../BRANCHING.md) for the full release and recovery
  flow.
- Read [`../SECURITY.md`](../SECURITY.md) for security reporting and protected
  evidence handling.
- Review the bounded workflow contracts under
  [`../.github/workflows/`](../.github/workflows/).
- Return an installation or enforcement finding to the authenticated
  repository administrator. The portable exports remain identifier-neutral.

## Return to repository root

[Return to the repository orientation](../README.md).
