# Contributing

Contributions should improve the maintained opportunity: data-contract
integrity, precise primitive findings, Practitioner Probes, or collaboration
orientation.

A schema change includes:

- one valid synthetic example;
- a focused test for the materially meaningful behavior;
- compatibility notes for affected consumers; and
- affirmative prose, comments, and identifiers.

Use JSON Schema 2020-12 and reuse definitions from `common.schema.json` where
they clarify meaning. Keep the contract direct. Use Flyway for PostgreSQL
migration mechanics, GitHub Rulesets for branch policy, GitHub secret scanning
and push protection for repository secrets, and Vale for prose checks.

## Local verification

```bash
python3 -m pip install --requirement requirements-dev.txt
python3 tools/validate_governance.py
vale --config=.vale.ini --no-global --minAlertLevel=warning .
python3 -m unittest discover -s tests -v
```

Reviewers examine semantic meaning, downstream compatibility, security and
privacy effects, target-state clarity, and focused test coverage.
