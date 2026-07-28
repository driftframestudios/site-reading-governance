# Migration from Schema Release 1.0 to 2.0

## Release intent

Schema release `2.0.0` implements Control Plane Profile `0.3.0`. It adds a
bounded-caller control spine, explicit veracity, flexible coordination,
machine-readable orientation, and future-reality receipt closure.

The major release reflects one breaking change: decision records gain required
probability context. Existing schema identifiers also move from `/v1.0/` to
`/v2.0/`.

## Required document changes

### Every governance record

1. Set `metadata.schema_version` to `2.0.0`.
2. Pin the governance release, commit, and digest used for validation.
3. Revalidate with the release `2.0.0` schema coordinate.

### Decision records

Add:

- `probability_of`
- `probability_horizon`
- `probability_basis`
- `probability_conditions`
- `recalibration_triggers`

Keep `falsifiers` as the observations that would overturn the selected
interpretation. The new fields define the event and conditions to which the
numeric probability applies.

### Repository orientation

Create:

- one `machine-node.schema.json` projection;
- one `first-receipt.schema.json` projection; and
- one `coordination-horizon.schema.json` projection.

Separate seed lineage from current repository provenance. Preserve
orientation-only authority in both orientation records.

### Automation callers

For each caller and write path:

1. define the bounded caller;
2. register the service-owned operation;
3. classify its effect;
4. define approval semantics;
5. produce effect and call-receipt records; and
6. verify replay and recovery behavior.

Broad and irreversible effects carry scoped approval before completion.

### Practitioner Probes and claims

Represent principal-level explanatory material with:

- one-through-five proficiency levels;
- review and repair surfaces;
- linked scenarios;
- linked claim-veracity records; and
- explicit instruction yield.

Every claim carries a veracity status, scope band, source provenance,
verification method, limitations, and recheck triggers.

### Four substantive receipt families

Use `simulated-receipt-closure.schema.json` when the collaboration selects a
future version of reality. The manifest:

- closes all four families exactly once;
- binds assumptions, source coordinates, executable checks, and artifacts;
- uses modeled authority roles;
- records `closed_in_simulation`; and
- preserves environment-observed closure as a separate, unasserted evidence
  state.

## Validation

Run:

```bash
make check
```

Successful migration produces:

- governance validation passed;
- negation-aware language check passed;
- secret-shape scan passed; and
- the complete regression suite passed.
