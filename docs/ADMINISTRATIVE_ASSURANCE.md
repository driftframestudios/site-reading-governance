# Review an administrative evidence packet

Receive a source-bound account before deciding what a result can support.
The companion places the proposed statement beside its evidence class,
population accounting, reviewer role, omitted dimensions, and correction route.
The initial profile serves local synthetic studies and modeled review.

## Try the smallest useful receipt

Python 3.11 or newer runs the capability example with the standard library:

```sh
python3 tools/assurance_companion.py \
  --request examples/assurance-request.json \
  --artifact capability=examples/assurance-capability.json --markdown
python3 -m unittest discover -s tests -p 'test_assurance_companion.py' -v
```

The result establishes admission of the supplied composition declaration.
Configured execution and remote caller authority retain pending standing.
The JSON and Markdown forms carry the same complete record. Output goes to
standard output; the receiving artifact owner controls retention and publication.

## Receive a complete study

Use an isolated Python environment with the optional `requirements-assurance.txt`
profile. The three source commits are explicit; package versions and source
coordinates carry separate meanings. Access to those repositories follows the
collaborating team's existing authorization.

```sh
python3 -m venv .venv-assurance
.venv-assurance/bin/python -m pip install -r requirements-assurance.txt
.venv-assurance/bin/python -m unittest discover -s tests -p 'test_assurance_upstream.py' -v
.venv-assurance/bin/python tools/assurance_companion.py \
  --request study-review-request.json \
  --artifact pack=scenario-pack.json \
  --artifact study=study.json \
  --artifact report=comparison.json
```

Start the request from `examples/assurance-request.json`. Name each artifact's
role, schema identity, exact-byte SHA-256, and reviewed source commit. A study
packet supplies pack, study, and report together. The `output_comparison` claim
uses the complete dependency set declared in `DEPENDENCIES` in the receiver.
The root schema documents every required field. Each human reviewer chooses the
exact proposed statement, intended use, omissions, and review role.

The receiver reads one bounded snapshot per supplied regular file and resolves
references from those supplied artifacts. Schema retrieval stays local. An
unresolved reference or changed digest returns a typed recovery code. Exact-byte
artifact digests and upstream canonical semantic digests are labeled separately.
A supplied commit identifies the proposed provenance coordinate; its acceptance
comes from source review. A matching digest establishes content identity.

## Compatibility and ownership

| Input | Meaning and admission owner | Governance receiving job |
| --- | --- | --- |
| Program study and run observations | Program `admit_administrative_study` and `interpret_administrative_study` | Carry population counts and specification/execution bindings |
| Simulation scenario pack | Simulation `admit_pack` | Bind authored source, oracle, cohort, and planned identities |
| Comparative report | Comparative typed report and `evaluate` | Require agreement with recomputation using the same admitted inputs |
| Workbench capability | Program's exact standalone capability schema | Keep composition separate from configured execution and caller authority |
| Claim and review | Governance claim-veracity, acceptance, invalidation, and this companion profile | Name intended use, reviewer, allowed interpretation, and next observation |

The comparator recomputation establishes receiving consistency. The authored
oracle and scientific interpretation retain separate review. Designed output
disagreements remain visible observations. Reportability, enrollment, coverage,
authorization, adjudication, payment, and responsibility retain distinct meanings
with Program and their applicable source owners.

The optional profile receives the current report through exact recomputation.
Comparative's dedicated report-admission Issue supplies the later reusable
receiver; migration can replace this adapter while preserving the companion.

## Review, correction, and recovery

`record_review` creates a distinct successor for one review-ready statement.
Its modeled reviewer and evidence ceiling remain explicit. `invalidate` creates
a successor that holds only statements depending on the changed bindings. Both
preserve the earlier record and bind its digest. A corrected study returns
through fresh source admission and scoring before review resumes.

The [runbook index](../.agents/runbooks/index.md) supplies population review,
decision recourse, change invalidation, and contract handoff. An automated
receiver prepares a reviewable account; accountable acceptance and production
authorization retain their own records and decision routes.

## Profile standing and extension

The companion is candidate profile 0.1 in the source workbench. Shared definitions
come from Governance's existing common schema. Its fixed role and claim enums
form deliberate compatibility boundaries. A later configured-execution or
organizational-acceptance profile supplies its evidence contract and versioned
migration. Public projection proceeds through the separately approved site release.

[Return to repository orientation](../README.md)

## Review entry and retained evidence

The receiver reconciles every supplied artifact digest with its named assessment
binding, binds the exact intended-use text, and requires the complete role-specific
binding set. The same eligibility rule governs initial admission and subsequent
review. An observation-free study retains its planned denominator and source
identities; its output-comparison claim stays held until completed, usable, and
scored observations are available. A capability response supports composition
review. Configured execution and population effects receive their own evidence.

A successor preserves the prior record and its digest. Policy or intended-use
changes hold dependent claims; unaffected composition claims retain their prior
standing. Fresh evidence enters through artifact admission. Companion validation
checks internal consistency. Source admission and accountable review establish
provenance and permitted use; a content digest identifies the supplied bytes.

### Focused exercise

Run the existing assurance test family in the contracts-enabled environment:

```sh
python -m unittest discover -s tests -p 'test_assurance_*.py' -v
```

The exercise uses the designed 144-run population: 136 attempted, 128 completed,
128 usable, 128 scored, four pending, four abstained, four failed, four excluded,
and zero cancelled. It checks each source binding against its named input owner,
retains a raw label including its surrounding spaces, reviews the fixture-level
comparison, holds a population-effect claim, and invalidates dependent claims after
policy and intended-use changes. The complete administrative decision, override,
and recourse procedures remain the next exercise under Issue #39.
