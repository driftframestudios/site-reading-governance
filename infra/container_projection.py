"""Admit one clean Governance source for its existing finite Pages builder.

Program's preparer, patch installer, and result publisher remain byte-identical
owners. This adapter owns the projection selection and its exact source capsule.
Preparation is O(source + wheel bytes); each runtime admission is O(source bytes).
All trees are operator-owned and quiescent. Receipts bind content, not approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_governance_pages as pages
import container_job as job
import container_runtime as runtime
from validate_governance import validate_pair

PROFILE = "infra/container-projection-profile.json"
REQUEST = "infra/projection-input.json"
JOB_SECONDS = 120
SUPPORT_EXAMPLES = {
    "assurance-request.json": "schemas/administrative-assurance.schema.json",
    "assurance-capability.json": "contract-resources/workbench-capabilities.v1.schema.json",
}
REQUIRED = {
    PROFILE, REQUEST, "AUTHORS", "LICENSE", "requirements-projections.txt",
    "infra/container_entry.py", "infra/container_projection.py",
    "infra/container_runtime.py", "infra/container_job.py", "infra/container_patch.py",
    "tools/build_governance_pages.py", "tools/schema_projections.py",
    "tools/validate_governance.py", "tools/automation_contract.py",
    "schemas/README.md", "examples/example-map.json",
    "schema-projections/promotion-receipt/v1.0.0/promotion-receipt.graphql",
    "schema-projections/promotion-receipt/v1.0.0/coverage.json",
    "contract-resources/assurance-source-map.json",
    *SUPPORT_EXAMPLES.values(),
    *("examples/" + name for name in SUPPORT_EXAMPLES),
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def record(path: str, content: bytes) -> dict:
    return {"path": path, "bytes": len(content), "sha256": sha256(content).hexdigest()}


def selected_profile(source: Path) -> tuple[bytes, job.Profile]:
    content = job.regular_bytes(source, PROFILE)
    profile = job.admitted_profile(job.strict_document(content))
    if (profile.name != "governance-projection" or profile.dependencies != "wheels"
            or list(profile.files) != sorted(profile.files)
            or not REQUIRED.issubset(profile.files)):
        raise job.ContextError("projection-profile")
    return content, profile


def exact_tree(root: Path, expected: set[str]) -> None:
    """Reject surplus files and directories, aliases, and unreadable subtrees."""
    observed = set()
    allowed_directories = {p.as_posix() for name in expected
                           for p in Path(name).parents if p != Path(".")}
    for directory, directories, files in os.walk(
        root, followlinks=False, onerror=runtime.traversal_failed,
    ):
        parent = Path(directory)
        for name in directories:
            child = parent / name
            if child.is_symlink() or child.relative_to(root).as_posix() not in allowed_directories:
                raise job.ContextError("projection-directory-membership")
        for name in files:
            relative = (parent / name).relative_to(root).as_posix()
            if relative not in expected:
                raise job.ContextError("projection-file-membership")
            observed.add(relative)
    if observed != expected:
        raise job.ContextError("projection-file-membership")


def locked_packages(content: bytes) -> dict[str, tuple[str, set[str]]]:
    if not job.requirements_admitted(content):
        raise job.ContextError("projection-lock")
    packages = {}
    for line in content.decode("ascii").replace("\\\n", " ").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        coordinate, *hashes = line.split()
        name, version = coordinate.split("==")
        name = re.sub(r"[-_.]+", "-", name).lower()
        if name in packages:
            raise job.ContextError("projection-lock-duplicate")
        packages[name] = (version, {value.removeprefix("--hash=sha256:") for value in hashes})
    return packages


def wheel_closure(lock: bytes, wheels: object) -> None:
    """The reviewed parser closure consists of one universal wheel per pin."""
    packages = locked_packages(lock)
    if not isinstance(wheels, list) or len(wheels) != len(packages):
        raise job.ContextError("projection-wheel-membership")
    observed = set()
    for item in wheels:
        if not isinstance(item, dict) or set(item) != {"file", "sha256"}:
            raise job.ContextError("projection-wheel-record")
        name = item["file"]
        if not isinstance(name, str):
            raise job.ContextError("projection-wheel-name")
        parts = name.split("-")
        if len(parts) != 5 or parts[2:] != ["py3", "none", "any.whl"]:
            raise job.ContextError("projection-universal-wheel")
        package = re.sub(r"[-_.]+", "-", parts[0]).lower()
        if package in observed or package not in packages:
            raise job.ContextError("projection-wheel-membership")
        version, hashes = packages[package]
        if parts[1] != version or item["sha256"] not in hashes:
            raise job.ContextError("projection-wheel-lock-binding")
        observed.add(package)
    if observed != set(packages):
        raise job.ContextError("projection-wheel-membership")


def validate_examples(source: Path) -> None:
    """Validate mapped Governance examples and the two declared support inputs."""
    document = job.strict_document(job.regular_bytes(source, "examples/example-map.json"))
    if not isinstance(document, dict) or set(document) != {"schema_map"}:
        raise job.ContextError("projection-example-map")
    mapping = document["schema_map"]
    if not isinstance(mapping, dict) or not mapping:
        raise job.ContextError("projection-example-map")
    for example, schema in mapping.items():
        if (re.fullmatch(r"[a-z][a-z0-9-]*[.]json", example) is None
                or not isinstance(schema, str)
                or re.fullmatch(r"[a-z][a-z0-9-]*[.]schema[.]json", schema) is None):
            raise job.ContextError("projection-example-path")
    if set(mapping) & SUPPORT_EXAMPLES.keys():
        raise job.ContextError("projection-support-example-map")
    if set(mapping) | SUPPORT_EXAMPLES.keys() | {"example-map.json"} != {p.name for p in (source / "examples").glob("*.json")}:
        raise job.ContextError("projection-example-membership")
    if set(mapping.values()) != {p.name for p in (source / "schemas").glob("*.schema.json") if p.name != "common.schema.json"}:
        raise job.ContextError("projection-schema-coverage")
    for example, schema in mapping.items():
        if validate_pair(source / "schemas" / schema, source / "examples" / example):
            raise job.ContextError("projection-example-admission")
    for example, schema in SUPPORT_EXAMPLES.items():
        if validate_pair(source / schema, source / "examples" / example):
            raise job.ContextError("projection-support-admission")


def prepare(source: Path, proof_path: Path, destination: Path, dependencies: Path,
            *, patches: Path, architecture: str, canonical_origin: str | None = None,
            cname: str | None = None) -> dict:
    """Stage through Program's preparer; publish the complete context receipt last."""
    source = pages._reject_symlink_components(source, "source root").resolve()
    proof = pages.load_source_proof(proof_path, source)
    profile_bytes, profile = selected_profile(source)
    origin = pages.normalize_canonical_origin(canonical_origin)
    hostname = pages.normalize_cname(cname, origin)
    if architecture not in ("arm64", "amd64"):
        raise job.ContextError("projection-platform")
    destination = pages._reject_symlink_components(destination, "context output")
    destination = destination.parent.resolve(strict=True) / destination.name
    for selected in (source, dependencies.resolve(), patches.resolve()):
        if destination.is_relative_to(selected) or selected.is_relative_to(destination):
            raise job.ContextError("external-context")
    if dependencies.is_symlink() or not dependencies.is_dir():
        raise job.ContextError("dependency-directory")
    lock, wheel_records = job.admitted_dependencies(dependencies)
    if lock != job.regular_bytes(source, "requirements-projections.txt"):
        raise job.ContextError("projection-source-lock")
    wheels = [{"file": name, "sha256": digest} for name, digest in sorted(wheel_records)]
    wheel_closure(lock, wheels)
    exact_tree(dependencies, {"requirements.lock", "wheel-manifest.json", *(w["file"] for w in wheels)})
    # Globbing owners receive their entire selected source family, including
    # non-public skills, so selection cannot conceal an added public-ready guide.
    for pattern in ("schemas/*.schema.json", "examples/*.json", ".agents/skills/*/SKILL.md"):
        if {p.relative_to(source).as_posix() for p in source.glob(pattern)} != {
            p for p in profile.files if Path(p).match(pattern)
        }:
            raise job.ContextError("projection-source-membership")
    validate_examples(source)
    acquired = False
    try:
        with tempfile.TemporaryDirectory(prefix=".projection-", dir=destination.parent) as temporary:
            work = Path(temporary)
            staged = work / "source"
            members = []
            for name in profile.files:
                if name == REQUEST:
                    continue
                content = job.regular_bytes(source, name)
                target = staged / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                members.append(record(name, content))
            request = {
                "version": "1.0.0", "sourceProof": pages.load_json(proof_path),
                "platform": f"linux/{architecture}", "canonicalOrigin": origin,
                "cname": hostname, "members": sorted(members, key=lambda r: r["path"]),
                "requirementsSha256": sha256(lock).hexdigest(), "wheels": wheels,
            }
            if pages._parse_source_proof(request["sourceProof"]) != proof:
                raise job.ContextError("projection-proof-changed")
            (staged / REQUEST).write_bytes(encoded(request))
            (staged / "infra/container-profile.json").write_bytes(profile_bytes)
            prepared = work / "context"
            job.prepare(staged, prepared, dependencies, patches=patches, architecture=architecture)
            dockerfile = (prepared / "Dockerfile").read_bytes() + b'CMD ["--profile", "projection"]\n'
            (prepared / "Dockerfile").write_bytes(dockerfile)
            receipt = job.strict_document((prepared / "context-receipt.json").read_bytes())
            receipt["members"] = [record("Dockerfile", dockerfile) if r["path"] == "Dockerfile" else r for r in receipt["members"]]
            receipt["projection"] = {"sourceRevision": proof.source_revision, "platform": request["platform"]}
            (prepared / "context-receipt.json").write_bytes(encoded(receipt))
            if pages.load_source_proof(proof_path, source) != proof:
                raise job.ContextError("projection-proof-changed")
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
            try:
                destination.mkdir(mode=0o700)
                acquired = True
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            for child in sorted(prepared.iterdir(), key=lambda p: (p.name == "context-receipt.json", p.name)):
                os.rename(child, destination / child.name)
            return {"status": "prepared", "profile": profile.name,
                    "sourceRevision": proof.source_revision, "platform": request["platform"],
                    "receiptSha256": sha256(encoded(receipt)).hexdigest()}
    except BaseException:
        if acquired:
            shutil.rmtree(destination)
        raise


def admit_prepared(source: Path, receipt_path: Path) -> tuple[pages.SourceProof, dict, dict]:
    profile_bytes, profile = selected_profile(source)
    exact_tree(source, set(profile.files))
    request_bytes = job.regular_bytes(source, REQUEST)
    request = job.strict_document(request_bytes)
    if not isinstance(request, dict) or set(request) != {
        "version", "sourceProof", "platform", "canonicalOrigin", "cname",
        "members", "requirementsSha256", "wheels",
    } or request["version"] != "1.0.0":
        raise job.ContextError("projection-input")
    proof = pages._parse_source_proof(request["sourceProof"])
    if proof.standing != "clean" or request["platform"] not in ("linux/arm64", "linux/amd64"):
        raise job.ContextError("projection-standing")
    origin = pages.normalize_canonical_origin(request["canonicalOrigin"])
    if origin != request["canonicalOrigin"] or pages.normalize_cname(request["cname"], origin) != request["cname"]:
        raise job.ContextError("projection-canonical-input")
    members = [record(name, job.regular_bytes(source, name)) for name in profile.files if name != REQUEST]
    if members != request["members"]:
        raise job.ContextError("projection-source-bytes")
    lock = job.regular_bytes(source, "requirements-projections.txt")
    if sha256(lock).hexdigest() != request["requirementsSha256"]:
        raise job.ContextError("projection-lock-digest")
    wheel_closure(lock, request["wheels"])
    receipt_bytes = job.regular_bytes(receipt_path.parent, receipt_path.name)
    receipt = job.strict_document(receipt_bytes)
    expected_source = sorted([
        {**item, "path": "source/" + item["path"]} for item in [*members, record(REQUEST, request_bytes)]
    ], key=lambda r: r["path"])
    if (not isinstance(receipt, dict) or receipt.get("version") != "1.0.0"
            or receipt.get("profile") != profile.name
            or receipt.get("profileSha256") != sha256(profile_bytes).hexdigest()
            or receipt.get("baseImage") != job.BASE_IMAGE
            or receipt.get("projection") != {"sourceRevision": proof.source_revision, "platform": request["platform"]}
            or not isinstance(receipt.get("members"), list)):
        raise job.ContextError("projection-context-receipt")
    records = receipt["members"]
    if (any(not isinstance(r, dict) or set(r) != {"path", "bytes", "sha256"} or not isinstance(r["path"], str) for r in records)
            or len({r["path"] for r in records}) != len(records)
            or [r for r in records if r["path"].startswith("source/")] != expected_source):
        raise job.ContextError("projection-context-source")
    if [r for r in records if r["path"] == "requirements.lock"] != [record("requirements.lock", lock)]:
        raise job.ContextError("projection-context-lock")
    if {r["path"]: r["sha256"] for r in records if r["path"].startswith("wheels/")} != {
        "wheels/" + w["file"]: w["sha256"] for w in request["wheels"]
    }:
        raise job.ContextError("projection-context-wheels")
    construction = {"version": "1.0.0", "sourceRevision": proof.source_revision,
                    "platform": request["platform"], "contextReceiptSha256": sha256(receipt_bytes).hexdigest(),
                    "projectionInputSha256": sha256(request_bytes).hexdigest(),
                    "requirementsSha256": request["requirementsSha256"], "wheels": request["wheels"]}
    return proof, request, construction


def produce(output: Path, source: Path = ROOT, receipt_path: Path = ROOT.parent / "context-receipt.json") -> None:
    _, request, construction = admit_prepared(source, receipt_path)
    for name, (version, _) in locked_packages(job.regular_bytes(source, "requirements-projections.txt")).items():
        if metadata.version(name) != version:
            raise job.ContextError("projection-installed-version")
    validate_examples(source)
    pages.build_site(source, source / REQUEST, output / "site",
                     canonical_origin=request["canonicalOrigin"], cname=request["cname"],
                     _proof_loader=lambda: admit_prepared(source, receipt_path)[0])
    (output / "construction.json").write_bytes(encoded(construction))


def validate(output: Path, source: Path = ROOT, receipt_path: Path = ROOT.parent / "context-receipt.json") -> None:
    _, request, construction = admit_prepared(source, receipt_path)
    if {p.name for p in output.iterdir()} != {"site", "construction.json"}:
        raise job.ContextError("projection-output-membership")
    if job.regular_bytes(output, "construction.json") != encoded(construction):
        raise job.ContextError("projection-construction-binding")
    manifest = pages.validate_site(output / "site", source, source / REQUEST,
                                  _proof_loader=lambda: admit_prepared(source, receipt_path)[0])
    if (manifest["publication"]["canonicalOrigin"] != request["canonicalOrigin"]
            or manifest["publication"]["cname"] != request["cname"]):
        raise job.ContextError("projection-publication-binding")


def run_projection() -> None:
    timed_out = False
    def interrupted(number, _frame):
        raise SystemExit(128 + number)
    def expired(_number, _frame):
        nonlocal timed_out
        timed_out = True
        # The shared publisher defers SIGTERM until acquisition records ownership.
        signal.raise_signal(signal.SIGTERM)
    previous_term = signal.signal(signal.SIGTERM, interrupted)
    previous = signal.signal(signal.SIGALRM, expired)
    signal.alarm(JOB_SECONDS)
    try:
        _, request, _ = admit_prepared(ROOT, ROOT.parent / "context-receipt.json")
        machine = {"aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
        if platform.system() != "Linux" or request["platform"] != f"linux/{machine}":
            raise job.ContextError("projection-runtime-platform")
        runtime.run(produce, validate=validate)
    except SystemExit as exc:
        if timed_out and exc.code == 128 + signal.SIGTERM:
            raise SystemExit(124) from None
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        signal.signal(signal.SIGTERM, previous_term)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--source-proof", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--patches", type=Path, required=True)
    parser.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    parser.add_argument("--canonical-origin")
    parser.add_argument("--cname")
    args = parser.parse_args()
    def interrupted(number, _frame):
        raise SystemExit(128 + number)
    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        result = prepare(args.source, args.source_proof, args.destination, args.dependencies,
                         patches=args.patches, architecture=args.architecture,
                         canonical_origin=args.canonical_origin, cname=args.cname)
    except (ValueError, OSError):
        print(json.dumps({"status": "held", "code": "projection-preparation"}))
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
