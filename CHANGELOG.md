# Changelog

All notable changes to this governance package appear here.

The format follows Keep a Changelog, and releases follow Semantic Versioning.

## [Unreleased]

## [1.0.0] — 2026-07-28

### Changed

- Bounded reusable-workflow inputs and schema-reference containment.
- Strict finite-number and RFC 3339 timestamp validation.
- Opaque governed evidence locators and protected constellation tag families.
- Lowercase forecast and evidence branch coordinates.
- Dependency-free secret-shape scanning with redacted findings.

### Migration

- Evidence artifact URLs move to opaque `governed://` or `evidence://`
  references.
- Date-time fields carry an RFC 3339 timezone.
- Release `1.0.0` supplies the successor coordinate because these security
  controls narrow the earlier accepted value set.

## [0.1.0] — 2026-07-28

### Added

- Governance and GitFlow-like branch contracts.
- Negation-aware language guidance and automated checking.
- JSON Schema contracts for constellation, specification, scenario, decision,
  simulation assumption, receipt, acceptance, comparison, and invalidation.
- Synthetic examples, reusable GitHub Actions workflows, repository templates,
  CODEOWNERS, and ruleset exports.
- Python standard-library validators and tests.
