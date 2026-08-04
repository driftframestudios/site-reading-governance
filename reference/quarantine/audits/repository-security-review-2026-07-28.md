# Repository security review — 2026-07-28

## Scope and verdict

This review covers the current authored trees of the five comparative-literacy
repositories and the 29 commit diffs that existed before the security-hardening
release:

- `lims-eln-program-specification`
- `lims-eln-enterprise-implementation`
- `lims-eln-simulated-final-state`
- `lims-eln-comparative-evidence`
- `site-reading-governance`

The current-tree and historical-diff scans found zero high-confidence credential
values, private keys, credential-bearing URLs, database connection strings, or
provider tokens. Synthetic identifiers, AWS resource references, secret names, and
redacted examples remain classified as references rather than credential values.

The review found several control weaknesses that could have admitted or exposed
protected values later. The successor releases close those paths and add regression
evidence.

## Review methods

The review combined:

1. high-confidence provider-token and private-key signatures;
2. generic secret-assignment and credential-bearing URL signatures;
3. authored-file, fixture, generated-artifact, and commit-diff inspection;
4. workflow permission, action identity, input-flow, and artifact-retention review;
5. evidence-admission, report-projection, tenant-boundary, and JSON-ingress review;
6. AWS runtime-configuration placement, IAM, KMS, caching, rotation, and telemetry
   review; and
7. repository-specific unit, schema, language, and artifact-boundary tests.

Scanner findings contain file, line, rule, and redacted length. Candidate values stay
outside scanner output.

## Material findings and dispositions

| Surface | Material finding | Successor disposition |
|---|---|---|
| Comparative evidence admission | An observation identifier could influence an output path, and accepted records trusted self-declared redaction too broadly. | Repository-safe identifiers, resolved-path containment, no-follow file creation, immutable supersession, strict provenance, independent identities, recursive protected-content checks, and acceptance-domain separation now gate admission. |
| Comparative reports | Difference reports could reproduce raw expected and observed values. | Difference values now use digest-only projections by default. A released comparison profile explicitly names any reportable paths. Generated reports pass an artifact secret-shape gate. |
| Reusable workflows | Caller-controlled values reached shell commands through direct expression interpolation. | Inputs now travel through quoted environment variables, bounded path grammars, canonical containment checks, immutable action identities, read-only permissions, and time limits. |
| JSON and schema validation | Duplicate keys, `NaN`, and infinite numbers could produce ambiguous parsing or bypass numeric bounds. | Strict JSON loaders reject duplicate keys and non-finite values. RFC 3339 timestamps carry explicit timezone information. |
| Tenant data | Several tenant-bearing PostgreSQL tables lacked a complete forced row-level-security posture. | Every tenant-bearing workload table now enables and forces row-level security with a fail-closed tenant setting. Governance-plane records have an explicit access-boundary rationale. |
| Simulation boundary | Synthetic-only use and migration or restore success were expressed mainly as prose or shared-code comparisons. | Executable synthetic-fixture admission, independent readback, failure twins, keyed pseudonymization, bounded output projections, and transient artifact scanning now carry the claim. |
| CI supply chain | Several workflows used movable action tags and retained checkout credentials by default. | Official actions use immutable commit identities, checkout persistence is disabled, permissions stay read-only, jobs have bounded duration, and uploaded evidence has explicit failure and retention behavior. |
| Runtime configuration | The implementation lacked a concrete AWS configuration and secret lifecycle. | Parameter Store carries named non-secret configuration. Secrets Manager carries named secret material. Exact-resource IAM, KMS service context, workload-role credentials, bounded in-memory caching, rotation-stage selection, value-free errors, and redacted telemetry are executable and tested. |

## AWS placement contract

The enterprise implementation creates configuration parameters and secret containers
while keeping secret values outside Terraform source and repository state. Secret
population occurs through an approved operational path. The application resolves:

- non-secret endpoints, timeouts, feature posture, and resource identifiers from
  AWS Systems Manager Parameter Store;
- vendor credentials, signing material, and pseudonymization keys from AWS Secrets
  Manager;
- request authority from the workload identity and standard AWS SDK credential
  provider chain; and
- decryption authority through the named KMS key and service encryption context.

The simulated-final-state repository carries the same contract through a deterministic
fake provider. Its receipts include references, versions, role, KMS key, cache policy,
and rotation posture while resolved values remain outside generated artifacts.

## Evidence boundaries

This historical review establishes repository-level evidence. At review time,
the following receipts were tracked for separate observed-state closure:

- enable and verify GitHub secret scanning and push protection for all five private
  repositories;
- apply and verify the exported branch, signature, tag, and required-check rulesets;
- validate CODEOWNERS identities and accountable reviewer availability;
- replace container version tags with reviewed immutable image digests;
- populate, rotate, revoke, and recover one production-shaped secret through the
  approved operational path;
- exercise workload-role denial, KMS-context denial, cache expiry, throttling, and
  rotation refresh in a configured AWS environment;
- run independent static analysis, dependency review, and an external application
  security assessment; and
- close the configured-vendor, representative migration and restore, production
  observability, and Scientific, Quality, and Regulatory acceptance receipts.

## Control Plane Profile v0.3 future-reality disposition

Schema release `2.0.0` adds an executable future-reality closure path. A pinned
simulation can close configured vendor environments, representative migration
and restore rehearsals, production security and observability, and modeled
Scientific, Quality, and Regulatory acceptance as
`closed_in_simulation`.

That manifest records environment-observed closure as a separate, unasserted
state and grants zero production authorization. This preserves the historical
review boundary while allowing the simulated constellation to reach a complete,
authentic future state using synthetic environments, modeled roles, executable
checks, and digest-bound artifacts.

## Release interpretation

`site-reading-governance` now advances to successor contract `2.0.0` because
probability context and the control-plane records shape downstream documents.
The implementation, simulation, comparator, and program specification align on
Control Plane Profile `0.3.0`. Historical release coordinates remain preserved
as lineage; current manifests bind to their repository-specific provenance
after GitFlow-like release merges.
