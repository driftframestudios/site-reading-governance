# Governance Pages source

The Governance Pages builder creates one reviewable retrieval artifact for the
accepted Governance 2.0.1 JSON Schemas. A visitor can find the right contract,
read its authority boundary in ordinary language, download the accepted bytes,
and recover the exact full-SHA source from every schema row.

The builder uses the Python standard library. It writes a new local artifact
directory and leaves repository refs, GitHub Pages settings, hosted branches,
custom-domain settings, and DNS at their current coordinates. A publication
receiver can inspect the artifact first, then select those hosted settings as a
separate human action.

## Source proof

Every build begins with a structured proof supplied by the release receiver:

```json
{
  "contractVersion": "1.0.0",
  "releaseAuthority": "Constellation release steward",
  "releaseStatus": "accepted",
  "releaseVersion": "2.0.1",
  "repository": "driftframestudios/site-reading-governance",
  "schemaCoordinate": "v2.0",
  "sourceRevision": "<accepted 40-character lowercase Git SHA>",
  "standing": "clean"
}
```

Keep this proof outside the source worktree. For `standing: clean`, the builder
requires the resolved source to be the Git worktree root for the named GitHub
repository, requires every configured `origin` URL to name that repository,
neutralizes caller-supplied Git redirection, reads the commit without local
replacement mappings, and resolves `HEAD^{commit}`. It rejects index flags that
mask worktree standing, compares every tracked regular file's bytes and
executable mode with its exact HEAD blob, and requires a zero-change tracked and
untracked worktree. The release authority supplies the accepted status; the
builder establishes the exact local source coordinate and clean standing.
Branch names alone carry neither claim.

Supply direct source, proof, and artifact paths. The builder keeps symbolic-link
components outside those caller-selected paths while retaining root-owned
operating-system path aliases. This makes the directory it reads or writes
visible at invocation time and keeps artifact inspection on the same path
contract as artifact construction.

The behavior suite uses `standing: fixture` explicitly. The production command
rejects fixture standing, so a test source cannot quietly acquire clean-release
standing.

## Build and verify

Use a clean worktree at the accepted source revision, a proof stored outside
that worktree, and a new output path outside the worktree:

```bash
python3 tools/build_governance_pages.py build \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-2.0.1

python3 tools/build_governance_pages.py verify \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-2.0.1
```

The output path must be new. This keeps cleanup an explicit artifact-owner
choice and protects a source tree or earlier comparison build from replacement.

For a reproducibility observation, build twice into two new directories and
compare every path and byte:

```bash
python3 tools/build_governance_pages.py build \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-first

python3 tools/build_governance_pages.py build \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-second

diff -qr /tmp/governance-pages-first /tmp/governance-pages-second
```

`make check` includes the builder behavior suite. That suite runs both isolated
builds, material mutation probes, exact schema-byte checks, manifest checks,
relative-link checks, and the generated-artifact secret-shape path.

## Artifact contract

The generated directory contains:

- `index.html`, `guidance/index.html`, and two progressively deeper schema
  discovery pages;
- `schemas/v2.0/*.schema.json`, copied byte for byte from the accepted source;
- `assets/site.css`, with responsive, keyboard-visible, reduced-motion, and
  forced-color behavior;
- `.nojekyll`;
- `manifest.json`; and
- `CNAME` only when the build receives an explicit matching canonical origin
  and hostname.

Every internal visitor link is relative. Every repository source link contains
the named repository and complete accepted SHA. Every artifact entry is a
self-contained regular file. Every HTML page carries organization author and
publisher metadata, one main landmark, one top-level heading, a skip link, the
two evaluation-data markers in their required order, a calm data-use
explanation, and the approved visible attribution footer projected from the
source-owned constant.

This repository currently contains no public-ready repository skill package,
so the artifact has no skill catalog. Internal and public-possible working
instructions remain with their existing controlled owners.

## Authority and evidence

Human-readable governance explains meaning, decision rights, evidence stages,
review, and recovery. The published JSON Schema bytes define machine-checkable
structure for Governance 2.0.1. A passing validation establishes structural
agreement with the selected schema. Scientific suitability, Quality or
Regulatory acceptance, environment qualification, and production authorization
receive their own evidence and accountable decision.

The deterministic manifest keeps these jobs distinct:

- `release` records the accepted version, coordinate, status, and accountable
  release role;
- `source` records the full revision, clean or fixture standing, and exact
  source-tree link;
- `authority` records human-readable, machine-validation, and publication
  roles;
- `schemas` records each identifier, source path and URL, output path, byte
  length, and SHA-256 digest;
- `publication` records every HTML page, every canonical page when an HTTPS
  origin is supplied, and the optional matching CNAME; and
- `inventory` records every generated file's bytes and SHA-256 digest except
  `manifest.json`, whose self-reference boundary is explicit.

The aggregate schema and content digests derive from that inventory. A digest
establishes content identity against the recorded bytes; human review and
material use establish meaning and suitability.

## Optional canonical origin and CNAME

The default build carries relative links, no canonical URL, and no CNAME. An
explicit HTTPS origin adds canonical metadata to every HTML page:

```bash
python3 tools/build_governance_pages.py build \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-canonical \
  --canonical-origin https://governance.example.org/contracts
```

An explicit CNAME adds the `CNAME` file when its hostname exactly matches the
canonical HTTPS hostname:

```bash
python3 tools/build_governance_pages.py build \
  --source-root /path/to/accepted-governance-source \
  --source-proof /path/to/governance-2.0.1-source-proof.json \
  --output /tmp/governance-pages-domain \
  --canonical-origin https://governance.example.org/contracts \
  --cname governance.example.org
```

These options shape a local artifact. Pages activation, hosted-source
selection, domain ownership, and DNS remain with the publication receiver.

## Generated-artifact safety

The repository secret-shape scanner includes HTML and CSS, so it can observe
the complete generated text surface:

```bash
python3 tools/scan_secret_shapes.py --root /tmp/governance-pages-2.0.1
```

A clean scan establishes zero detector matches in the named artifact. Service
settings, hosted responses, unfetched history, forks, and later receiving
copies retain their own observation paths.
