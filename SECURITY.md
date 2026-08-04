# Security Policy

## Reporting

Share suspected vulnerabilities through the repository's private security
advisory channel. Include the affected release, reproduction conditions,
potential material effect, and a safe contact route.

Vulnerability details and working exploit material stay in the private advisory.
The response team uses least-privilege access and records the resulting repair
through the ordinary reviewed change path.

## Repository data

Examples contain synthetic identifiers and scientific data. Credentials,
personal data, regulated records, tenant payloads, and signed storage URLs stay
in approved stores and enter repository documentation only as redacted
references.

Repository administrators enable GitHub secret scanning and push protection.
GitHub remains the source of repository-level secret detection and prevention;
provider-side credential monitoring and rotation remain active as defense in
depth.

## Dependencies and workflows

GitHub Actions references use immutable commit SHAs. Dependabot proposes
dependency updates through ordinary pull requests. Workflow permissions remain
read-only unless a documented operation requires a narrower explicit write.

The Python validation dependency is pinned in `requirements-dev.txt` and
reviewed through Dependabot.
