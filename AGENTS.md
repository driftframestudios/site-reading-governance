# Site Reading Governance collaboration ground

This repository defines the shared schema and governance contracts used across
the LIMS/ELN repository suite. Make changes here when a shared record shape,
language rule, release coordinate, or governance boundary needs to change.

## Begin with current source

- Run `git status --short --branch` and read the latest local and remote
  history.
- Read [`README.md`](README.md), [`GOVERNANCE.md`](GOVERNANCE.md),
  [`BRANCHING.md`](BRANCHING.md), and the four root orientation records before
  changing a contract.
- Use [`schemas/README.md`](schemas/README.md) to locate the schema that owns a
  document shape. Use [`promotion-receipt.json`](promotion-receipt.json) when
  the accepted tag, commit, archive digest, or release status changes a
  decision.
- Use [`coordination-horizon.json`](coordination-horizon.json) for current work
  and re-entry. Released contracts and runnable source continue to define
  behavior.
- Preserve unrelated work already present in the worktree.

## Keep authority roles clear

- [`GOVERNANCE.md`](GOVERNANCE.md) explains meaning, decision rights, evidence
  stages, review, and recovery.
- The tracked files in [`schemas/`](schemas/) define machine-checkable document
  structure for the named schema release.
- A release receipt binds an accepted tag, commit, and reproducible archive
  digest after protected promotion.
- Governance Pages projects accepted schema and skill bytes for retrieval. Its
  manifest establishes artifact identity and completeness.
- Accountable scientific, Quality, Regulatory, security, operational, and
  business roles retain suitability, acceptance, and authorization decisions.

Use
[`governance-schema-release-lineage`](.agents/skills/governance-schema-release-lineage/SKILL.md)
when one schema needs to be followed from tracked source through its release
coordinate and byte-identical Pages copy. The map keeps schema meaning, release
acceptance, projection evidence, hosted delivery, and downstream use as
distinct facts.

Use
[`repository-reentry`](.agents/skills/repository-reentry/SKILL.md)
when resumed work needs current branch, release, orientation, and collaboration
state reconstructed before a change.

Use
[`source-authority-mapping`](.agents/skills/source-authority-mapping/SKILL.md)
when a claim, language rule, schema family, example, release record, or Pages
projection crosses several meaning, validation, acceptance, delivery, or
downstream-use roles. The focused schema-release skill remains the smaller
route when one schema and its exact retrieval copy are the whole decision.

Use
[`contextual-jargon-scan`](.agents/skills/contextual-jargon-scan/SKILL.md)
in stride when public or cross-repository prose may assume local context.
Retain exact schema, release, Git, and regulatory terms; define useful compact
language and revise shorthand whose object or consequence remains unclear.

These three skills remain public-possible while natural use tests their local
fit. Governance Pages continues to project only reviewed public-ready skills.

## Use the accepted branch route

- `main` carries reviewed governance releases; `develop` integrates the next
  release.
- Begin ordinary work from `develop` on `feature/`, `fix/`, or `chore/` and
  return it to `develop` through review.
- Form `release/<semver>` when a named release candidate is assembled. Form a
  `hotfix/` from `main` for an accepted release repair, then merge that repair
  forward into `develop`.
- Follow [`BRANCHING.md`](BRANCHING.md) for the complete release and evidence
  route.

## Write for a public reader

- Lead instructions with the state collaborators can create or verify.
- Pair a hard safety, privacy, or scope boundary with the affirmative behavior
  that keeps the work useful.
- Use ordinary language around exact schema, Git, and regulatory terms. Define
  repository shorthand where it first changes a decision.
- Keep private working locators with their authorized lineage owners. Public
  guidance points to repository-local or accepted public sources.
- Keep personal attribution in the repository's approved carriers. Commit,
  Issue, pull-request, and review prose stays focused on the change.

The public language authority is
[`docs/NEGATION_AWARE_LANGUAGE.md`](docs/NEGATION_AWARE_LANGUAGE.md). Its
executable policy and exact reviewed corpus live in [`language-policy/`](language-policy/).

## Validate the material behavior

The complete source-owned proof uses Python 3.11 or newer and the standard
library:

```sh
make check
```

Run the deterministic Pages proof from a clean commit when schema retrieval,
public-ready skills, or Pages source changes. Follow
[`docs/GOVERNANCE_PAGES.md`](docs/GOVERNANCE_PAGES.md) to supply an external
proof for the exact commit, build twice into new directories, compare every
byte, verify one artifact, and scan its generated text for credential-shaped
values.

## Close with one clear receiver

Return the changed source, the smallest observation that establishes its
behavior, its evidence limit, and the repository or accountable role that can
make the next decision. A release coordinate stays pending until the protected
promotion path supplies its accepted commit, tag object, archive digest, and
later receipt carrier.
