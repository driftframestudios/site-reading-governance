# Site Reading Governance

Site Reading Governance is the shared rulebook and record format for a
five-repository laboratory information management and electronic lab notebook
(LIMS/ELN) collaboration. It gives teams stable schemas, worked examples,
release evidence, language rules, and review boundaries so a plan,
implementation result, simulation, comparison, or acceptance decision can
travel with its meaning and authority intact.

Repository authorship and maintenance provenance is recorded in
[`AUTHORS`](AUTHORS). Git history and reviewed pull requests preserve change
chronology and contribution credit.

## Start with a result and its evidence

Use Governance to make a result understandable to the next reviewer: what was
observed, what decision is being considered, who can accept it, and what would
prompt a revision. The [schema guide](schemas/README.md) connects the record
families with their examples and validation routes.

For example, take a laboratory comparison and identify the source evidence,
intended use, review authority, and acceptance decision. Keep the observed
result and the decision as related records so a future reviewer can inspect
both. Program's [constellation starting guide](https://github.com/driftframestudios/lims-eln-program-specification/blob/main/docs/README.md)
shows how that handoff connects to the workbench and comparison tools.

Insurance and administrative studies can start from the existing evidence and
decision grammar. The dedicated provenance, population-claim, and decision
assurance extensions are owned by
[#38](https://github.com/driftframestudios/site-reading-governance/issues/38).
The shared administrative meanings stay with Program; Governance describes
how evidence, review, recourse, and acceptance support their use.

## Review an administrative evidence packet

The [assurance guide](docs/ADMINISTRATIVE_ASSURANCE.md) receives digest-bound
scenario, study, comparison, and capability records. Start with the local
capability example, then use the optional upstream profile for a complete
study. Each companion separates the proposed statement, evidence class,
review authority, omitted dimensions, and correction route.

The [runbook index](.agents/runbooks/index.md) routes population review,
decision recourse, invalidation, and contract handoff. These source-level
profiles prepare reviewed work; publication follows its tagged release gate.

The [database lifecycle receiver](docs/DATABASE_LIFECYCLE_ASSURANCE.md) uses a
separate pinned Program profile to receive declared resource ownership,
operation outcomes, and recovery state. It keeps configured execution and
accountable acceptance visible as separate pending claims.

## Current state

The release line and the later evidence line answer different questions:

| Coordinate | Current role | Read next |
| --- | --- | --- |
| Annotated `governance-v2.2.0` tag | Identifies the accepted Governance 2.2.0 source subject on the protected `main` release line | [`STATUS.md`](STATUS.md) for the time-bounded source snapshot and [`BRANCHING.md`](BRANCHING.md) for the lifecycle |
| `develop` | Carries the later observed release receipt and accepted-source Governance Pages publication evidence | The [four orientation records](#orientation-records) at the `develop` coordinate |
| Promotion-receipt projection family | Retains candidate standing while JSON Schema remains its validation authority | [`schema-projections/README.md`](schema-projections/README.md) |
| Downstream repositories | Choose when Governance 2.2.0 adoption becomes material and validate their own representative records | [`docs/ADOPTION.md`](docs/ADOPTION.md) |

The files in the tagged source tree describe the state that was knowable when
the release subject formed. The same root record paths on `develop` carry the
later observation. Read the four records from one branch coordinate at a time;
when comparing the release subject with its later evidence, name both roles.
This keeps the signed tag stable while current collaboration remains easy to
recover.

## Choose your route

| Task | Start here | Continue with |
| --- | --- | --- |
| Understand the governance model and decision rights | [`GOVERNANCE.md`](GOVERNANCE.md) | [`STATUS.md`](STATUS.md) for its time-bounded source snapshot and the [orientation records](#orientation-records) for later evidence |
| Find or validate a record shape | [`schemas/README.md`](schemas/README.md) | [`examples/example-map.json`](examples/example-map.json) and [`docs/ADOPTION.md`](docs/ADOPTION.md) |
| Resume repository work | [`first-receipt.json`](first-receipt.json) and [`coordination-horizon.json`](coordination-horizon.json) | [`repository-reentry`](.agents/skills/repository-reentry/SKILL.md) |
| Audit a schema release from source to retrieval | [`promotion-receipt.json`](promotion-receipt.json) | [`governance-schema-release-lineage`](.agents/skills/governance-schema-release-lineage/SKILL.md) and [`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) |
| Distinguish meaning, validation, release, delivery, and use | [`source-authority-mapping`](.agents/skills/source-authority-mapping/SKILL.md) | The [evidence and authority map](#evidence-and-authority) |
| Review public or cross-repository wording | [`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md) | [`language-policy/README.md`](language-policy/README.md) and [`contextual-jargon-scan`](.agents/skills/contextual-jargon-scan/SKILL.md) |
| Change schemas, documentation, or repository policy | [`CONTRIBUTING.md`](CONTRIBUTING.md) | [`BRANCHING.md`](BRANCHING.md), [`SECURITY.md`](SECURITY.md), and [`rulesets/README.md`](rulesets/README.md) |

## Quickest proof

Python 3.11 or newer can run the dependency-free governance validator:

```bash
python3 tools/validate_governance.py
```

That command establishes the declared JSON schema, example, orientation,
workflow, ruleset, release-receipt, and repository-route contracts it checks.
The complete source-owned proof installs two exact, hash-locked parsers and
adds projection, language, secret-shape, and regression evidence:

```bash
python3 -m pip install --disable-pip-version-check --require-hashes \
  -r requirements-projections.txt
make check
```

Passing checks establish executable agreement at the inspected revision.
Material suitability, hosted behavior, downstream adoption, and accountable
acceptance retain their own reviews and evidence.

## Orientation records

The four root JSON files form one re-entry set:

| Record | Reader job | Authority boundary |
| --- | --- | --- |
| [`machine-node.json`](machine-node.json) | Identify the repository role, provenance, consumers, campaigns, and source-handling classes | Orientation only; released policy and authenticated operations authorize effects |
| [`first-receipt.json`](first-receipt.json) | Receive a compact evidence posture, source permissions, and handoff | Orientation only; the named source and accountable role own each decision |
| [`coordination-horizon.json`](coordination-horizon.json) | See sequenced work, retained effects, consequential questions, and the next safe action | Coordinates work; its evidence owners establish completion |
| [`promotion-receipt.json`](promotion-receipt.json) | Distinguish candidate readiness from an observed tag, commit, archive digest, and later receipt carrier | The protected release route and recorded evidence establish release standing |

Use [`repository-reentry`](.agents/skills/repository-reentry/SKILL.md) when the
records, branches, or publication surfaces appear to describe different
moments. The result names settled release state, current source, open evidence,
and one exact next move.

## Contract journey

The shortest governance journey is:

```text
meaning and decision rights
  -> versioned schema
  -> synthetic example and executable check
  -> protected release subject and promotion receipt
  -> byte-identified retrieval copy
  -> downstream use and accountable acceptance
```

For database change, the record family adds the operational steps that make a
transition inspectable:

```text
data contract
  -> refactor finding
  -> migration plan
  -> migration receipt
  -> data reconciliation
  -> database release manifest
```

[`GOVERNANCE.md`](GOVERNANCE.md) defines the assurance lifecycle from
`specified` through `accepted`, the simulation boundary, bounded callers,
invalidation, comparison, and review. The schema catalog links each stage to
its machine-checkable record.

## Evidence and authority

| Role | Source owner | What it establishes |
| --- | --- | --- |
| Meaning and decision rights | [`GOVERNANCE.md`](GOVERNANCE.md) and focused guides | The intended distinctions, review roles, and recovery model |
| Machine-checkable structure | [`schemas/`](schemas/) | The fields and invariants a selected document must satisfy |
| Representative use | [`examples/`](examples/) | Synthetic records that exercise the declared contracts |
| Executable agreement | [`tools/`](tools/) and [`tests/`](tests/) | The behavior covered by the named validators and assertions |
| Release acceptance | [`promotion-receipt.json`](promotion-receipt.json), [`release-receipts/`](release-receipts/), and the annotated tag | The accepted source coordinate and its recorded evidence |
| Retrieval identity | [`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) and the generated manifest | The bytes, paths, and source relation of the public copy |
| Material use and acceptance | Each receiving repository and accountable scientific, Quality, Regulatory, security, operational, or business role | Fitness and authorization for the stated context |

One source can carry several roles. Name the relation—such as `defines`,
`validates`, `exemplifies`, `accepts`, `projects`, or `consumes`—when that
distinction changes a decision.

## Collaboration guides

Four repository-local skill contracts support bounded work:

| Task | Guide | Declared standing |
| --- | --- | --- |
| Trace one schema through release and Pages | [`governance-schema-release-lineage`](.agents/skills/governance-schema-release-lineage/SKILL.md) | `public_ready`; included in the reviewed Pages projection |
| Reconstruct branch, release, orientation, and live work state | [`repository-reentry`](.agents/skills/repository-reentry/SKILL.md) | `public_possible`; retained in the source workbench |
| Map several source and authority roles | [`source-authority-mapping`](.agents/skills/source-authority-mapping/SKILL.md) | `public_possible`; retained in the source workbench |
| Replace collaboration-local shorthand while preserving exact terms | [`contextual-jargon-scan`](.agents/skills/contextual-jargon-scan/SKILL.md) | `public_possible`; retained in the source workbench |

The frontmatter of each guide records its current source band and lineage.
Governance Pages projects the reviewed `public_ready` contract. Natural use and
review provide the evidence for any later standing change. A runbook catalog
can begin when a settled multi-phase procedure exists in this repository.

## Constellation

| Repository role | Purpose | Authority |
| --- | --- | --- |
| Program specification | Intent, examples, risks, forecasts, and acceptance criteria | Desired behavior |
| Enterprise implementation | Current code, infrastructure, migrations, and runbooks | Running implementation |
| Simulated final state | Executable counterfactual with explicit assumptions | Forecast behavior |
| Comparative evidence | Fixtures, normalizers, paired runs, and divergence adjudication | Comparison record |
| Site Reading Governance | Shared schemas, workflows, templates, and policy exports | Governance contract |

Runtime code flows from the program specification into each implementation
through released, digest-pinned contracts. Learning returns through reviewed
decision records. The actual implementation and simulated final state retain
independent source histories.

## Repository map

- [`STATUS.md`](STATUS.md) — time-bounded release and capability snapshot
- [`GOVERNANCE.md`](GOVERNANCE.md) — meaning, authority, evidence, review, and
  recovery
- [`BRANCHING.md`](BRANCHING.md) — branch lifecycle and release protocol
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution and local-verification
  contract
- [`schemas/README.md`](schemas/README.md) — clickable schema catalog,
  invariants, and evolution
- [`schema-projections/README.md`](schema-projections/README.md) — candidate
  YAML and GraphQL projection family
- [`examples/example-map.json`](examples/example-map.json) — schema-to-example
  membership
- [`docs/ADOPTION.md`](docs/ADOPTION.md) and the migration guides in
  [`docs/`](docs/) — downstream use and version transitions
- [`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) — deterministic public
  retrieval artifact and handoff
- [`language-policy/README.md`](language-policy/README.md) — executable language
  policy assets and exemption lifecycle
- [`release-receipts/README.md`](release-receipts/README.md) — historical
  observed release records
- [`rulesets/README.md`](rulesets/README.md) — reviewable GitHub ruleset request
  bodies
- [`.github/workflows/`](.github/workflows/) — bounded repository and reusable
  validation workflows
- [`audits/`](audits/) — repository security and dependency-automation reviews
- [`tools/`](tools/) and [`tests/`](tests/) — validators, builders, scanners,
  and behavior contracts

## Versioning and adoption

Schema releases follow semantic versioning:

- a major release can require an intentional document migration;
- a minor release adds compatible capability; and
- a patch release repairs validation, examples, or explanation while
  preserving accepted document behavior.

Governance 2.2.0 retains the stable `/v2.0/` schema identifiers. Consumers pin
the annotated release tag, accepted commit, and SHA-256 digest of
`git archive --format=tar <commit>`. Floating branches support exploration;
governed comparisons use immutable release coordinates. Start downstream work
with [`docs/ADOPTION.md`](docs/ADOPTION.md) and the matching migration guide.

## Source posture

[`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md) is the
public authority for this repository's applied language posture. It explains
desired-state guidance, hard-boundary treatment, automated checks, and the
local verification path. The versioned executable policy and reviewed corpus
live in [`language-policy/`](language-policy/).

Public collaboration prose uses repository-local or accepted public sources.
Private working coordinates remain with their authorized lineage owner while a
semantic title, role, evidence standing, and next route preserve the useful
relationship here.

## Confined container job

The [finite container entry](infra/README.container-job.md) reuses the constellation's
prepared-input and confined-runtime safeguards. Its source profile, focused
checks, output ownership, and release-evidence boundary remain inspectable.
