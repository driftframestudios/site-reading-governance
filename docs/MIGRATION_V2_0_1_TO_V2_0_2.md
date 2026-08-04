# Migration from 2.0.1 to 2.0.2

Schema release `2.0.2` retains the stable `/v2.0/` identifier coordinate and
adds an executable database-contract representation for enterprise laboratory
data. Existing contract consumers can stage adoption by validating their
current records, adding the new profile and isolation surfaces, and then
pinning the promoted `governance-v2.0.2` coordinate.

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
7. Run governance validation and retain the resulting receipt with the pinned
   release coordinate.

The governance contract describes the required target state and remains
migration-tool neutral. Repository-owned migration tooling continues to own
ordering, checksums, execution serialization, and schema history.
