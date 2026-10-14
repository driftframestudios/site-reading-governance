# Confined finite container job

This repository uses the prepared-input and confined-runtime pattern from Enterprise's reviewed container work. The profile in [container-profile.json](container-profile.json) owns the exact admitted source files and this repository's finite job. The shared preparation helper is owned by Program; [container-support.json](container-support.json) binds the receiving copy.

## Prepare and run

Choose a reviewed source checkout or a verified source-carrier component. Keep it quiescent during preparation. This route records content digests; the accepted source receipt supplies Git lineage separately. Select new external context and output directories through shell variables. The output directory belongs to the invoking non-root user.

```sh
mkdir -m 700 "$LIMS_JOB_OUTPUT" &&
uv run --isolated --no-project --python 3.12 --managed-python -- \
  python infra/container_job.py "$LIMS_JOB_CONTEXT" --patches "$LIMS_JOB_PATCHES" --architecture "$LIMS_JOB_ARCHITECTURE" &&
export LIMS_RUNTIME_UID="$(id -u)" LIMS_RUNTIME_GID="$(id -g)" &&
docker compose -f infra/container-compose.yml build &&
docker compose -f infra/container-compose.yml run --rm job
```

This core profile uses standard-library behavior and the admitted source resources. Optional Program conformance and complete repository/release suites retain their existing dependency and proof routes.

## Ownership and recovery

The image has a non-root default. Compose selects the non-root owner of the host output directory, a read-only root, one writable output mount, bounded temporary storage, dropped capabilities, privilege-escalation protection, process/memory/CPU bounds, and a network-disabled finite job. The job checks its ordinary identity and output ownership before writing. Runtime credentials and daemon sockets are outside this profile.

Each invocation produces a new run directory containing its complete native artifacts under `payload/` and a sibling `job-receipt.json`. Simulation and Comparison apply their native artifact validators before publication. Earlier runs retain their names and bytes. Ordinary failure or termination cleans the owned pending directory. A forced kill or host failure can leave a pending directory; retain it for private inspection, then remove only that invocation's incomplete directory. The completed marker establishes a complete generated set at return, rather than power-loss durability. Context preparation requires a fresh external destination and writes its complete receipt last; a failed preparation can be repeated with a fresh destination.

## Evidence and release

Run the focused tests with the existing unittest discovery pattern:

```sh
uv run --isolated --no-project --python 3.12 --managed-python -- \
  python -m unittest discover -s tests -p 'test_container_*.py' -v
```

The fixture tests cover exact context membership, declared byte digests, path/file boundaries, clean failure, retained output, and configuration. A configured run must additionally establish the selected platform and actual confinement, repeatable output, image/dependency findings, and a fresh secret canary. Base-image identity and vulnerability status are separate observations. Tagging remains held by the five-repository hardening gate until those results and independent review are accepted. Existing hosted triggers, private-history proofs, main review protection, and publication settings retain their owners.

[Docker build secrets](https://docs.docker.com/build/building/secrets/) and [Compose service controls](https://docs.docker.com/reference/compose-file/services/) supply the upstream contract.

## Review and extension boundary

The source tree and dependency directory are operator-owned and quiescent during preparation. Each copied file is bounded and digest-bound; staged directories receive mode 0755 and copied files mode 0644 inside the private mode-0700 context. Program owns the shared preparation, runtime, and installer modules and their receiving-copy digests. Each repository owns its finite entry, native parser, native artifact validator, and exact source profile.

The runtime inspects every emitted member and propagates directory traversal failures. Native artifact families retain their own exact inventories under `payload/`; container metadata stays beside that family. A successful rename publishes one complete invocation. Retry creates a new invocation while prior completed runs retain their bytes.

[Research and design decisions](https://github.com/driftframestudios/lims-eln-program-specification/blob/main/infra/container-design-evidence.md) connect the shared implementation to primary sources and focused counterexamples. Current image findings and actual Compose behavior remain separate release evidence.

## Reviewed base, native repair, and installer inputs

Set `LIMS_JOB_ARCHITECTURE` to `arm64` or `amd64` and
`LIMS_JOB_PATCHES` to an operator-owned directory outside the checkout and
prepared context. List the selected native package and installer wheel with:

```sh
uv run --isolated --no-project --python 3.12 --managed-python -- \
  python infra/container_patch.py "$LIMS_JOB_ARCHITECTURE"
```

Acquire the listed HTTPS URLs under their listed filenames. The records carry
exact byte counts and SHA-256 hashes; context preparation admits those bytes
using the existing bounded regular-file reader. Extra directory entries stay
outside the prepared context. Keep acquisition separate from the build so the
application installer remains offline.

The pinned Python 3.12.15 slim Trixie base supplies Debian 13 runtime packages.
Its network-disabled guard verifies the release and architecture, checks the
selected native package hash and metadata, and installs `liblzma5` version
`5.8.1-1+deb13u2` before the installer and runtime stages diverge. The exact
ARM64 and AMD64 package records follow Debian's signed security package indices.
The package's `libc6 >= 2.34` dependency is satisfied by the pinned base.
Installation must finish with the expected configured version and architecture.
The shared base and final image also exercise Python's native `lzma` decoder
against fixed XZ and legacy LZMA streams and bounded round trips. These checks
establish package state and codec behavior; the
[Debian security update](https://security-tracker.debian.org/tracker/DSA-6549-1)
and [upstream advisory](https://github.com/tukaani-project/xz/security/advisories/GHSA-5qpq-xqfv-j9pg)
provide the remediation scope. Later native updates enter through a reviewed
base revision or another exact, separately admitted package revision. A separate
installer stage receives `pip==26.2.1`, bound to its PyPI release hash. The
installer verifies the wheel again inside a network-disabled build step using a
read-only temporary mount. The runtime base removes its pinned installer package,
metadata, scripts, and
`ensurepip` bootstrap route. The separate installer stage runs the verified
pip wheel, confirms patched pip, and installs the complete application closure
into an explicit prefix. `--ignore-installed` ensures that prefix contains the
required packages independently of the installer's global environment.

The final stage receives only the application prefix at its matching
`/usr/local` coordinates. Build-time checks confirm that pip and ensurepip import
routes, pip distribution metadata, and pip executables remain absent. These are
finite job images; editable environments and dependency changes use the existing
researcher environment route and a rebuilt, reviewed image.

The newer pip/vendor layers stay in the installer stage. Original upstream base
layers retain their historical bytes, including the earlier native library; the
package repair and installer removal establish the final runtime filesystem
boundary. Build-time tooling retains its own advisory review under
the offline, hash-admitted invocation. This follows Docker's
[multi-stage build](https://docs.docker.com/build/building/multi-stage/) ownership
pattern and pip's [prefix installation](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-prefix)
contract with the same Python interpreter layout in each stage.

The context receipt includes the verified native package, installer wheel, and generated bootstrap lock.
Program owns the shared patch module and its copy-local digest binding alongside
the preparer.

Both architecture selections are declared. Configured runtime and vulnerability
observations identify their exercised platform separately. A package update
provides evidence for its addressed findings; remaining findings retain their
component-specific review and human acceptance boundary. Image approval, main
promotion, and public source tagging remain separately owned decisions.

## Confined Governance Pages projection

Issue #52 adds a separately selected `governance-projection` profile. The
default `container_job.py` route above remains standard-library-only. The
[projection adapter](container_projection.py) selects the exact files in
[container-projection-profile.json](container-projection-profile.json), admits
the existing hash-locked parser closure, and calls the existing
[`build_governance_pages.py`](../tools/build_governance_pages.py) builder and
verifier. It introduces no second renderer or projection implementation.

The source receiver supplies the existing external
[Pages source proof](../docs/GOVERNANCE_PAGES.md#source-proof). Preparation checks
its exact clean Git worktree before and after staging. The proof's release
authority and acceptance fields remain receiver assertions; a successful build
establishes construction, not a new release acceptance. The runtime carries
that proof and an exact content inventory in `infra/projection-input.json`.
The builder's private admission hook rechecks that snapshot at its ordinary
before-build, verification, and before-handoff gates. The public builder CLI
continues to require its external proof and Git checks. Fixture standing remains
test-only. Git history, credentials, and daemon sockets stay outside the image.

### Prepare the selected inputs

Use a clean, named source revision and an isolated Python 3.12 environment.
Select fresh external context and dependency directories and an existing owned
patch directory. The lock currently names three universal wheels: the YAML and
GraphQL parsers plus the declared typing dependency. Downloading happens before
the offline image build:

```sh
mkdir -m 700 "$LIMS_PROJECTION_DEPENDENCIES" &&
"$LIMS_PYTHON" -m pip download --require-hashes --only-binary=:all: --no-deps \
  -r requirements-projections.txt -d "$LIMS_PROJECTION_DEPENDENCIES" &&
cp requirements-projections.txt "$LIMS_PROJECTION_DEPENDENCIES/requirements.lock"

"$LIMS_PYTHON" - "$LIMS_PROJECTION_DEPENDENCIES" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
document = {
    "version": "1.0.0",
    "requirementsSha256": sha256((root / "requirements.lock").read_bytes()).hexdigest(),
    "wheels": [{"file": p.name, "sha256": sha256(p.read_bytes()).hexdigest()}
               for p in sorted(root.glob("*.whl"))],
}
with (root / "wheel-manifest.json").open("x") as stream:
    json.dump(document, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

"$LIMS_PYTHON" infra/container_projection.py "$LIMS_JOB_CONTEXT" \
  --source-proof "$LIMS_PROJECTION_PROOF" \
  --dependencies "$LIMS_PROJECTION_DEPENDENCIES" \
  --patches "$LIMS_JOB_PATCHES" --architecture "$LIMS_JOB_ARCHITECTURE"
```

The preparer admits exactly one universal wheel per source pin and its allowed
hash, and rejects surplus dependency entries. Every executed Python owner,
schema, mapped example, source catalog, GraphQL/coverage input, and scanned skill
source is declared. Templates and CSS remain constants in the source-owned
builder. Source-family omissions, changed prepared bytes, surplus prepared
files/directories, and lock drift hold the job. Mapped examples pass their native
schema-pair validator; full cross-record/release suites remain separate checks.
Optional `--canonical-origin` and `--cname` keep the existing HTTPS and matching
hostname contract and default to absent. Use identical settings for each build.

### Build, run, and inspect

Use the same Compose command and confinement settings as the core job. The
projection context selects `--profile projection` through its image command.
The finite projection process adds a 120-second wall-clock deadline to the
existing process, CPU, memory, and scratch limits. Dependencies install from the
prepared closure with network disabled. The runtime has network disabled and a
read-only image; its writable paths remain the owned output mount and bounded
scratch space.

```sh
mkdir -m 700 "$LIMS_JOB_OUTPUT" &&
export LIMS_RUNTIME_UID="$(id -u)" LIMS_RUNTIME_GID="$(id -g)" &&
docker compose -p governance-projection -f infra/container-compose.yml build &&
docker compose -p governance-projection -f infra/container-compose.yml run --rm job
```

Each completed run contains `payload/site/`, the unchanged native Pages family,
and `payload/construction.json`, its source/platform/context/dependency binding.
The existing `job-receipt.json` inventories both. Pages `manifest.json` retains
its self-hash exclusion; the outer job receipt includes that manifest's bytes.
The native verifier runs before the finite-job publisher renames the complete
run. Retry uses a new run name and preserves every prior run. Partial writes,
producer errors, native verification failures, output collisions, SIGTERM, and
the projection deadline clean only owned pending work. Forced-kill/host-failure
recovery follows the pending-directory inspection route above.

Inspect the actual container configuration and final image ID locally. Bind
that observed image ID and platform to the context receipt digest, job receipt
digest, source revision, dependency lock/wheel hashes, and site manifest digest
in the receiving evidence record. A source declaration or base digest alone
does not establish the final image's identity or confinement. Keep raw inspect
output and local paths in the operator's local evidence directory.

### Focused acceptance and recovery evidence

```sh
"$LIMS_PYTHON" -B -m unittest discover -s tests -p 'test_container_projection.py' -v
"$LIMS_PYTHON" -B -m unittest discover -s tests -p 'test_governance_pages.py' -v
"$LIMS_PYTHON" -B -m unittest discover -s tests -p 'test_schema_projections.py' -v
```

The projection fixtures use real clean temporary Git sources, native builders,
and independent complete byte maps. Synthetic wheel and patch bytes exercise
admission only; configured image installation supplies package-execution
evidence. Fault fixtures cover source and dependency membership, exact lock
binding, malformed/missing examples, projection drift, changed source/proof,
observed dependency versions, partial output, real termination, collisions, and
retention of prior context/output bytes.

For configured acceptance, build the native site once and run two separately
prepared contexts in isolated containers, then compare complete relative path
sets and every byte of both `payload/site/` trees with the native result. Verify
each site with the public native verifier against the original clean source and
external proof. Run the repository secret-shape scanner against the generated
artifact, first demonstrating its detector with a fresh non-issued canary in an
owned temporary fixture. Record the exact platform and final image, actual
runtime controls, dependency/image scan scope and database age, normalized
findings, and accountable dispositions. Prior base/installer exceptions retain
their component-specific scope; new parser/runtime findings receive their own
review.

The resulting evidence and independent review return to Issue #43. Its remaining
projection criterion and the all-five carrier gate in Program #65 stay with
their named receivers. Source acceptance, construction evidence, carrier
readiness, merge, tagging, and publication remain distinct decisions. This
profile is independent of the administrative-assurance work in Issue #39.
