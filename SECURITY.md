# Security Policy

## Reporting

Share suspected vulnerabilities through the repository's private security
advisory channel. Include the affected release, reproduction conditions,
potential material effect, and a safe contact route.

**SAFETY BOUNDARY:** vulnerability details and working exploit material must not enter public issues or ordinary pull-request discussion; the replacement behavior is a private security advisory with access limited to the response team, and the advisory access review verifies that boundary.

## Supported releases

The current major release and the immediately preceding major release receive
security review. Release notes identify any narrower support window.

## Repository data

Examples contain synthetic identifiers and synthetic scientific data. Evidence
manifests can contain digests and opaque `governed://` or `evidence://`
locators. Query credentials, user information, fragments, and signed storage
URLs remain in the approved evidence system.

**PRIVACY BOUNDARY:** credentials, personal data, regulated records, and unredacted tenant payloads must not enter Git history; the replacement behavior is storage in the approved evidence system with redaction, retention, audit, and least-privilege controls, and the repository content scan verifies that committed examples contain synthetic data or redacted locators.

## Dependency posture

The local validator uses the Python standard library. GitHub Actions references
are pinned to immutable commit SHAs in production releases. Maintainers review
action updates through ordinary pull requests with provenance and permission
analysis.

The dependency-free secret-shape scan reports file, line, rule, and redacted
length. Protected values remain absent from scanner output.
