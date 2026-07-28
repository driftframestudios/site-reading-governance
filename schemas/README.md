# Schema Catalog

All contracts use JSON Schema 2020-12 and stable HTTPS identifiers.
Release `1.0.0` uses the stable `/v1.0/` identifier coordinate.

| Schema | Record |
| --- | --- |
| `constellation.schema.json` | Repository topology, authority, and release policy |
| `specification.schema.json` | Desired behavior, rules, scenarios, and acceptance roles |
| `scenario.schema.json` | Given/When/Then example with material effect and recovery |
| `decision.schema.json` | Selected option, alternatives, forecast, and falsifiers |
| `simulation-assumption.schema.json` | Time-bounded assumption, basis, owner, and falsifiers |
| `receipt.schema.json` | Environment-bound assurance evidence |
| `acceptance.schema.json` | Scientific, Quality, Regulatory, and other accountable decisions |
| `comparison.schema.json` | Pinned actual/simulation result and adjudication |
| `invalidation.schema.json` | Change-triggered re-evaluation and successor evidence |
| `common.schema.json` | Shared identifiers, actors, artifacts, metrics, and boundaries |

## Contract invariants

- Simulated receipts use simulation authority and retain actual acceptance as an
  explicit future gate.
- Accepted receipts use observed evidence, organizational authority, and a named
  accountable approver.
- Simulated acceptance records remain projections.
- Actual accountable acceptance uses observed evidence.
- Governance records close their property surface to make drift visible.
- Hard safety, privacy, and Regulatory boundaries include protected state,
  explicit constraint, replacement behavior, and verification.

## Consumer pinning

Downstream repositories pin the governance release, commit, and digest. The
reusable contract workflow validates each document with the selected schema from
that immutable coordinate.

Artifact locators use opaque `governed://` or `evidence://` references. Date-time
values carry an RFC 3339 timezone, and numeric values remain finite.

## Evolution

Compatible fields arrive in minor releases. Consumer-shaping changes arrive in
major releases with examples, migration guidance, and invalidation analysis.
