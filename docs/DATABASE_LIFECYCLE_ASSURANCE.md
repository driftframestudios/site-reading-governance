# Receive a declared database lifecycle

Governance receives one lifecycle record through Program's packaged semantic
admission, then prepares a bounded assurance summary. The receiver preserves
declared ownership, the requested profile, operation outcomes, recovery
references, and unresolved resources. Its `declared_lifecycle` evidence ceiling
keeps configured execution and accountable acceptance pending. A readiness
declaration, capability composition, or successful operation record can inform
the next review; runtime evidence and accountable decisions establish those
later claims.

## Source and receiving ownership

[The accepted source map](../contract-resources/database-lifecycle-source.json)
binds Program's exact Git revision, package version, lifecycle schema identity
and digest, and capability-v1 schema digest. Program owns the closed shape and
semantic admission. Governance selects this source independently of incoming
records and checks installed package and schema identity before admission.
Install the exact Git requirement in a caller-controlled environment. Admission
checks its [PEP 610 origin metadata](https://packaging.python.org/en/latest/specifications/direct-url-data-structure/)
for the repository, requested full revision, and resolved commit; requires a
wheel installation; and binds the imported package and lifecycle module paths
to that distribution's installed files. The same check verifies package version
and both schema byte digests.

The source map also records Program's existing
`path-length-bytes-sha256-v1` package-source digest. The receiving proof verifies
that digest from the exact Git revision using Program's
`scripts.validate_program.package_source_digest_from_git` helper. Program's
release coordinate owns its scope and algorithm; the local admission path
checks installation provenance and schema bytes. The caller retains control
of the Python environment and its installed metadata.

[`tools/lifecycle_assurance.py`](../tools/lifecycle_assurance.py) owns the local
claim mapping. The immutable assessment contains raw and canonical input
digests, the accepted source map, declared evidence class, ownership, readiness,
composition, outcome counts, and unresolved resource references. The
`recorded_operations` count includes succeeded, failed, and unresolved events;
requested events have their own count. A successful retry resolves the current
resource state while the summary retains earlier failure counts. Callers retain
the digest-bound input to recover the complete event history.

The receiver performs local JSON admission and returns JSON to standard output.
Database creation, credentials, migrations, restore, cleanup, authenticated
authority, scientific suitability, and operational acceptance retain their
existing runtime and accountable owners. Semantic `ref:` keys keep private
resource coordinates with those owners.

## Run the optional receiver

Use a dedicated Python 3.12-or-newer environment for Program's package:

```sh
python3 -m pip install -r requirements-lifecycle.txt
python3 tools/lifecycle_assurance.py --lifecycle examples/database-lifecycle-assurance.json
python3 -m unittest tests.test_lifecycle_assurance -v
```

Add `--capability <owned-capability-file>` when the lifecycle declares observed
capability composition. Both inputs must be regular files within 128 KiB each.
The final file entry must be a regular file; retain path ownership with the
caller. Admission compares exact capability bytes with the declared digest and
requires the PostgreSQL form of capability v1. Composition remains distinct
from dependency readiness, shared-contract compatibility, and authority.

The example is an authored cleanup-failure scenario. It establishes a usable
receiving route with one unresolved resource, while its configured execution
and acceptance remain pending. The output belongs to the caller; choose an
owned retention destination when the next review needs a durable artifact.

The separate [administrative study profile](../requirements-assurance.txt)
retains its accepted Program 0.6.1 coordinate. The lifecycle profile uses the
additive Program 0.7.0 API and unchanged lifecycle 1.0.0 schema bytes. Governance's
base validator remains dependency-free on Python 3.11 or newer. Full source checks continue through
`make check` after the exact projection parser dependencies are installed.
Optional lifecycle tests skip explicitly when the lifecycle module is absent;
installed dependency failures remain visible.

## Independent receiving observations

[`tests/test_lifecycle_assurance.py`](../tests/test_lifecycle_assurance.py)
authors Governance-specific records and literal expectations. Its fixtures and
expected results are independent of Program's and Enterprise's tests. Program's
admission is the exercised implementation; source validation output supplies
none of the expected results.

The tests distinguish disposable, retained, and external ownership; constrain
external cleanup to the declared owner decision; retain failed and unresolved
cleanup history; end ownership evidence at a resource incarnation boundary;
bind migration compatibility; reject stale source, schema, and version claims;
and combine exact capability-v1 bytes without raising the evidence ceiling.
They also check immutable returns, caller-owned exported documents, bounded
file reads, and value-free CLI findings.

This receiving proof advances
[Program #79](https://github.com/driftframestudios/lims-eln-program-specification/issues/79)
and the lifecycle portion of
[Governance #49](https://github.com/driftframestudios/site-reading-governance/issues/49).
Issue #49 retains configured execution, recovery evidence, remote authority,
and accountable acceptance work with its named owners. The existing
[administrative assurance guide](ADMINISTRATIVE_ASSURANCE.md) continues to own
the closed study companion and its review lifecycle.

[Return to the repository](../README.md).
