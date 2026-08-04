# Contributing

## Contribution contract

Each contribution keeps governance, executable contracts, examples, and tests in
concordance. A schema change travels with:

- a decision or issue reference;
- at least one valid example;
- a focused validation test;
- compatibility and invalidation analysis;
- clear migration guidance when consumers must act;
- data-primitive rationale, supported upgrade paths, bounded execution, and
  recovery evidence when database meaning changes;
- desired-state language across prose, comments, and identifiers.

## Local verification

```bash
python3 tools/validate_governance.py
python3 tools/check_language.py
python3 -m unittest discover -s tests -v
```

Vale `3.15.2` can provide advisory author feedback with
`vale --config=.vale.ini .`. The deterministic commands above remain the
candidate-eligibility controls.

## Schema design

- Use JSON Schema draft 2020-12.
- Give each schema a stable HTTPS `$id`.
- Close governance records with `additionalProperties: false`.
- Reuse definitions from `common.schema.json`.
- Represent important distinctions as enums or conditional contracts.
- Require provenance, evidence mode, assurance stage, and ownership where the
  record makes an assurance claim.
- Pair each hard safety or privacy boundary with its replacement behavior and
  observable verification.
- Express database changes through the data contract, finding ledger, migration
  plan, execution receipt, reconciliation, and release manifest as applicable.
- Preserve applied migration files and checksums; reviewed successor migrations
  carry each later change.
- Use native database primitives for governed meaning and exact strings for
  decimal-valued evidence interchange.

## Review

Reviewers examine:

1. semantic meaning and intended material effect;
2. machine validation and downstream compatibility;
3. evidence and authority separation;
4. security, privacy, and retention effects;
5. affirmative, verifiable language;
6. tests that exercise success, boundary, failure-twin, and recovery behavior.
7. database lock, compatibility, reconciliation, restore, and accountable
   acceptance evidence when the contribution changes persisted meaning.

## Sensitive reports

Security disclosures follow [`SECURITY.md`](SECURITY.md). Regulated evidence and
tenant details follow the governed-store boundary in [`GOVERNANCE.md`](GOVERNANCE.md).
