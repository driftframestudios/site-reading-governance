# Adopting a Maintained Contract

1. Pin a reviewed governance release.
2. Copy or reference the required maintained schema.
3. Add a repository-specific synthetic example.
4. Validate with a JSON Schema 2020-12 implementation.
5. Add focused tests for the semantic behavior the contract protects.
6. Use GitHub Rulesets and protected branches for repository delivery policy.

A downstream repository can call the reusable validation workflow with a
maintained schema:

```yaml
jobs:
  data-contract:
    uses: driftframestudios/site-reading-governance/.github/workflows/reusable-contract-validation.yml@<commit-sha>
    with:
      governance_repository: driftframestudios/site-reading-governance
      governance_ref: <commit-sha>
      schema_name: data-contract.schema.json
      document_path: documentation/data-contract.json
    secrets:
      governance_read_token: ${{ secrets.GOVERNANCE_READ_TOKEN }}
```

The fine-grained token carries read access to the governance repository. Both
checkouts disable credential persistence. Runtime behavior continues through
the downstream application's established platforms.
