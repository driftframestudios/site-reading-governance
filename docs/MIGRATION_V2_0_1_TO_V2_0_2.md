# Data-contract migration into 3.0.0

Schema release `3.0.0` adds a focused database-contract representation for
enterprise laboratory data. Consumers can stage adoption by validating current
records, adding the profile and isolation surfaces, and pinning a reviewed 3.0.0
release.

## Adoption sequence

1. Add `representation_id` and declare database supported-major and canonical
   JSON profiles.
2. Define tenant isolation, internal and external identity, scientific numeric,
   unit vocabulary, digest, and write-policy profiles.
3. Bind every entity to a tenant scope and write policy. Tenant-owned primary
   keys and foreign keys lead with tenant identity, and forced row-level
   security carries a reviewable policy digest.
4. Bind each instant to a temporal role and finite-value requirement. Event
   records preserve distinct occurrence and recording instants.
5. Bind scientific quantities to source and canonical values, source and UCUM
   units, assay and method revision, conversion factor, rounding policy,
   mapping revision, and provenance digest.
6. Represent append-only behavior, supersession, and controlled table
   privileges through write policies and enforced constraints.
7. Run JSON Schema validation and focused semantic tests with the pinned release.

Flyway owns ordering, checksums, execution serialization, and schema history for
repository-owned PostgreSQL. Vendor tooling owns vendor database lifecycle.
