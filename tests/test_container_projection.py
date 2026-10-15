"""Behavioral admission, native equality, and recovery for the projection profile."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))
import container_projection as projection
from container_patch_fixtures import patch_inputs

PARSERS = importlib.util.find_spec("graphql") and importlib.util.find_spec("ruamel")


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class CompleteSourceTests(unittest.TestCase):
    def test_complete_repository_families_have_explicit_receiving_owners(self):
        _, profile = projection.selected_profile(ROOT)
        projection.validate_source_families(ROOT, profile)
        projection.validate_examples(ROOT, complete_source=True)
        self.assertNotIn("examples/database-lifecycle-assurance.json", profile.files)
        self.assertEqual(projection.RECEIVER_EXAMPLES["database-lifecycle-assurance.json"],
                         "tools/lifecycle_assurance.py")


@unittest.skipUnless(PARSERS, "install requirements-projections.txt for projection behavior")
class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.source = self.root / "source"
        self.source.mkdir()
        self.profile = json.loads((ROOT / projection.PROFILE).read_bytes())
        source_inputs = (set(self.profile["files"])
                         | {"examples/" + name for name in projection.RECEIVER_EXAMPLES}
                         | set(projection.RECEIVER_EXAMPLES.values()))
        for name in source_inputs:
            if name == projection.REQUEST:
                continue
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.dependencies = self.root / "dependencies"
        self.dependencies.mkdir()
        self.wheels = []
        requirements = []
        for name, version in (("graphql_core", "3.3.0"), ("ruamel_yaml", "0.19.1"), ("typing_extensions", "4.16.0")):
            filename = f"{name}-{version}-py3-none-any.whl"
            content = ("synthetic admission fixture: " + filename).encode()
            digest = sha256(content).hexdigest()
            (self.dependencies / filename).write_bytes(content)
            self.wheels.append({"file": filename, "sha256": digest})
            requirements.append(f"{name}=={version} --hash=sha256:{digest}\n")
        lock = "".join(requirements).encode()
        (self.dependencies / "requirements.lock").write_bytes(lock)
        (self.source / "requirements-projections.txt").write_bytes(lock)
        (self.dependencies / "wheel-manifest.json").write_bytes(projection.encoded({
            "version": "1.0.0", "requirementsSha256": sha256(lock).hexdigest(), "wheels": self.wheels,
        }))
        self.patches = self.enterContext(patch_inputs())
        self.git("init", "--quiet", "--initial-branch=fixture")
        self.git("remote", "add", "origin", "https://github.com/driftframestudios/site-reading-governance.git")
        self.proof_path = self.root / "proof.json"
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args],
                                       env=projection.pages._git_environment(), stderr=subprocess.PIPE, text=True).strip()

    def commit(self):
        self.git("add", "--all")
        self.git("-c", "user.name=Projection fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "--allow-empty", "-m", "Projection fixture")
        self.proof_path.write_bytes(projection.encoded({
            "contractVersion": "1.0.0", "releaseAuthority": "Constellation release steward",
            "releaseStatus": "accepted", "releaseVersion": "2.2.0",
            "repository": "driftframestudios/site-reading-governance", "schemaCoordinate": "v2.0",
            "sourceRevision": self.git("rev-parse", "HEAD"), "standing": "clean",
        }))

    def prepare(self, name="context", **options):
        context = self.root / name
        projection.prepare(self.source, self.proof_path, context, self.dependencies,
                           patches=self.patches, architecture="arm64", **options)
        return context

    def publish(self, context, producer=None):
        output = self.root / "output"
        output.mkdir(exist_ok=True)
        source = context / "source"
        receipt = context / "context-receipt.json"
        result = projection.runtime.publish(
            producer or (lambda p: projection.produce(p, source, receipt)), output,
            validate=lambda p: projection.validate(p, source, receipt),
        )
        return output / result["directory"]

    def test_exact_source_dependency_and_receipt_membership(self):
        context = self.prepare()
        observed = tree(context)
        expected = {"source/" + p for p in self.profile["files"]} | {
            "Dockerfile", "requirements.lock", "context-receipt.json",
            "security-patches/pip.lock", "security-patches/pip-26.2.1-py3-none-any.whl",
            "security-patches/liblzma5_5.8.1-1+deb13u2_arm64.deb",
        } | {"wheels/" + w["file"] for w in self.wheels}
        self.assertEqual(set(observed), expected)
        receipt = json.loads(observed["context-receipt.json"])
        self.assertEqual({r["path"] for r in receipt["members"]}, expected - {"context-receipt.json"})
        for item in receipt["members"]:
            self.assertEqual(item["bytes"], len(observed[item["path"]]))
            self.assertEqual(item["sha256"], sha256(observed[item["path"]]).hexdigest())
        self.assertTrue(observed["Dockerfile"].endswith(b'CMD ["--profile", "projection"]\n'))
        projection.admit_prepared(context / "source", context / "context-receipt.json")

    def test_native_and_two_prepared_builds_have_identical_complete_bytes(self):
        options = {"canonical_origin": "https://governance.example.org/contracts", "cname": "governance.example.org"}
        native = self.root / "native"
        projection.pages.build_site(self.source, self.proof_path, native, **options)
        first = self.publish(self.prepare("first", **options))
        second = self.publish(self.prepare("second", **options))
        expected = tree(native)
        self.assertEqual(len(expected), 44)
        self.assertEqual(tree(first / "payload/site"), expected)
        self.assertEqual(tree(second / "payload/site"), expected)
        manifest = json.loads(expected["manifest.json"])
        self.assertEqual(manifest["inventory"]["excludes"], ["manifest.json"])
        self.assertEqual({r["path"] for r in manifest["inventory"]["files"]}, set(expected) - {"manifest.json"})
        for run in (first, second):
            receipt = json.loads((run / "job-receipt.json").read_bytes())
            self.assertEqual({r["path"] for r in receipt["files"]}, {"payload/" + name for name in tree(run / "payload")})
            self.assertEqual(len(receipt["files"]), 45)

    def test_integrated_assurance_inputs_retain_declared_owners_and_bytes(self):
        expected = {
            "schemas/administrative-assurance.schema.json",
            "examples/administrative-assurance.json",
            "examples/assurance-request.json",
            "examples/assurance-capability.json",
            "contract-resources/workbench-capabilities.v1.schema.json",
            "contract-resources/assurance-source-map.json",
        }
        self.assertTrue(expected.issubset(self.profile["files"]))
        mapping = json.loads((self.source / "examples/example-map.json").read_bytes())["schema_map"]
        self.assertEqual(mapping["administrative-assurance.json"], "administrative-assurance.schema.json")
        self.assertTrue({"assurance-request.json", "assurance-capability.json"}.isdisjoint(mapping))
        context = self.prepare()
        for name in expected:
            with self.subTest(name=name):
                self.assertEqual((context / "source" / name).read_bytes(), (ROOT / name).read_bytes())
        copied = context / "source/contract-resources/workbench-capabilities.v1.schema.json"
        provenance = json.loads((context / "source/contract-resources/assurance-source-map.json").read_bytes())
        self.assertEqual(provenance["capability_schema"]["byte_digest"], "sha256:" + sha256(copied.read_bytes()).hexdigest())

    def test_support_inputs_use_native_schema_admission_without_site_packages(self):
        code = "import sys; sys.path.insert(0,'infra'); import container_projection as p; from pathlib import Path; p.validate_examples(Path('.'), complete_source=True); assert not {'schema_projections', 'assurance_upstream', 'lifecycle_assurance', 'lims_eln_contracts', 'graphql', 'ruamel'} & sys.modules.keys()"
        subprocess.run([sys.executable, "-B", "-S", "-c", code], cwd=self.source,
                       check=True, capture_output=True)

    def test_lifecycle_example_retains_its_separate_receiver_and_source_bytes(self):
        example = self.source / "examples/database-lifecycle-assurance.json"
        owner = self.source / "tools/lifecycle_assurance.py"
        before = (example.read_bytes(), owner.read_bytes())
        context = self.prepare()
        self.assertFalse((context / "source/examples/database-lifecycle-assurance.json").exists())
        self.assertFalse((context / "source/tools/lifecycle_assurance.py").exists())
        self.publish(context)
        self.assertEqual((example.read_bytes(), owner.read_bytes()), before)

    def test_complete_source_requires_each_declared_receiver_input_and_owner(self):
        for name in ("examples/database-lifecycle-assurance.json", "tools/lifecycle_assurance.py"):
            with self.subTest(name=name):
                path = self.source / name
                content = path.read_bytes()
                path.unlink()
                self.commit()
                with self.assertRaises((ValueError, OSError)):
                    self.prepare()
                self.assertFalse((self.root / "context").exists())
                path.write_bytes(content)
                self.commit()

    def test_lifecycle_example_keeps_its_owner_outside_the_projection_profile_and_map(self):
        example = "examples/database-lifecycle-assurance.json"
        profile_path = self.source / projection.PROFILE
        original = profile_path.read_bytes()
        profile_path.write_bytes(projection.encoded({
            **self.profile, "files": sorted([*self.profile["files"], example]),
        }))
        self.commit()
        with self.assertRaisesRegex(ValueError, "projection-receiver-example"):
            self.prepare()
        profile_path.write_bytes(original)
        mapping_path = self.source / "examples/example-map.json"
        mapping = json.loads(mapping_path.read_bytes())
        mapping["schema_map"][Path(example).name] = "administrative-assurance.schema.json"
        mapping_path.write_bytes(projection.encoded(mapping))
        self.commit()
        with self.assertRaisesRegex(ValueError, "projection-support-example-map"):
            self.prepare()
        self.assertFalse((self.root / "context").exists())

    def test_missing_malformed_and_schema_invalid_support_inputs_hold_preparation(self):
        for name in ("assurance-request.json", "assurance-capability.json"):
            path = self.source / "examples" / name
            original = path.read_bytes()
            invalid = json.loads(original)
            if name == "assurance-request.json":
                invalid["profile_version"] = "9.0.0"
            else:
                invalid["runtime"]["state_lifetime"] = "database"
            for value in (None, b"{malformed", projection.encoded(invalid)):
                with self.subTest(name=name, value=value):
                    if value is None:
                        path.unlink()
                    else:
                        path.write_bytes(value)
                    self.commit()
                    with self.assertRaises(ValueError):
                        self.prepare()
                    self.assertFalse((self.root / "context").exists())
                    path.write_bytes(original)
                    self.commit()

    def test_support_inputs_keep_their_owners_outside_the_governance_map(self):
        path = self.source / "examples/example-map.json"
        original = path.read_bytes()
        for name in ("assurance-request.json", "assurance-capability.json"):
            with self.subTest(name=name):
                document = json.loads(original)
                document["schema_map"][name] = "administrative-assurance.schema.json"
                path.write_bytes(projection.encoded(document))
                self.commit()
                with self.assertRaisesRegex(ValueError, "projection-support-example-map"):
                    self.prepare()
                self.assertFalse((self.root / "context").exists())
        path.write_bytes(original)
        self.commit()

    def test_surplus_support_input_is_rejected_even_when_declared_in_profile(self):
        name = "examples/extra-assurance.json"
        (self.source / name).write_bytes((self.source / "examples/assurance-request.json").read_bytes())
        for declared in (False, True):
            with self.subTest(declared=declared):
                if declared:
                    altered = {**self.profile, "files": sorted([*self.profile["files"], name])}
                    (self.source / projection.PROFILE).write_bytes(projection.encoded(altered))
                self.commit()
                with self.assertRaisesRegex(ValueError, "projection-example-membership" if declared else "projection-source-membership"):
                    self.prepare()
                self.assertFalse((self.root / "context").exists())

    def test_stdlib_validation_entry_operates_without_site_packages(self):
        code = "import sys; sys.path.insert(0,'infra'); import container_entry; from pathlib import Path; container_entry.produce(Path(sys.argv[1])); assert 'schema_projections' not in sys.modules"
        output = self.root / "stdlib"
        output.mkdir()
        subprocess.run([sys.executable, "-B", "-S", "-c", code, str(output)], cwd=self.source,
                       check=True, capture_output=True)
        self.assertEqual(json.loads((output / "validation.json").read_bytes())["status"], "passed")

    def test_dirty_source_and_fixture_proof_hold_preparation(self):
        (self.source / "LICENSE").write_text("changed")
        with self.assertRaisesRegex(ValueError, "zero changes"):
            self.prepare()
        self.assertFalse((self.root / "context").exists())
        self.commit()
        proof = json.loads(self.proof_path.read_bytes())
        proof["standing"] = "fixture"
        self.proof_path.write_bytes(projection.encoded(proof))
        with self.assertRaisesRegex(ValueError, "fixture standing"):
            self.prepare()

    def test_profile_cannot_omit_an_executed_owner_or_schema(self):
        for name in ("tools/schema_projections.py", "schemas/receipt.schema.json",
                     "schemas/administrative-assurance.schema.json",
                     "examples/assurance-request.json", "examples/assurance-capability.json",
                     "contract-resources/workbench-capabilities.v1.schema.json",
                     "contract-resources/assurance-source-map.json"):
            with self.subTest(name=name):
                altered = {**self.profile, "files": [p for p in self.profile["files"] if p != name]}
                (self.source / projection.PROFILE).write_bytes(projection.encoded(altered))
                self.commit()
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse((self.root / "context").exists())

    def test_missing_changed_and_malformed_examples_hold_preparation(self):
        path = self.source / "examples/receipt.json"
        for value in (None, b"{}\n", b"{malformed"):
            with self.subTest(value=value):
                if value is None:
                    path.unlink()
                else:
                    path.write_bytes(value)
                self.commit()
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse((self.root / "context").exists())

    def test_projection_drift_fails_native_owner_before_publication(self):
        (self.source / "schema-projections/promotion-receipt/v1.0.0/coverage.json").write_text("{}")
        self.commit()
        context = self.prepare()
        with self.assertRaisesRegex(ValueError, "candidate schema projection differs"):
            self.publish(context)
        self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_surplus_dependency_is_rejected_instead_of_silently_ignored(self):
        (self.dependencies / "surplus.whl").write_bytes(b"surplus")
        with self.assertRaisesRegex(ValueError, "membership"):
            self.prepare()
        self.assertFalse((self.root / "context").exists())

    def test_different_lock_or_unlisted_wheel_hash_cannot_change_the_closure(self):
        original = (self.dependencies / "requirements.lock").read_bytes()
        (self.dependencies / "requirements.lock").write_bytes(original + b"# changed\n")
        with self.assertRaisesRegex(ValueError, "locked-requirements"):
            self.prepare()
        (self.dependencies / "requirements.lock").write_bytes(original)
        changed = [dict(w) for w in self.wheels]
        changed[0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "lock-binding"):
            projection.wheel_closure(original, changed)
        (self.dependencies / self.wheels[0]["file"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "wheel-byte-mismatch"):
            self.prepare()
        self.assertFalse((self.root / "context").exists())

    def test_prepared_missing_surplus_and_changed_source_fail_before_output(self):
        for kind in ("missing", "surplus", "changed", "directory"):
            with self.subTest(kind=kind):
                context = self.prepare(kind)
                source = context / "source"
                if kind == "missing":
                    (source / "examples/receipt.json").unlink()
                elif kind == "surplus":
                    (source / "tools/extra.py").write_text("raise RuntimeError()")
                elif kind == "directory":
                    (source / "empty-surplus").mkdir()
                else:
                    with (source / "tools/build_governance_pages.py").open("a") as stream:
                        stream.write("\n# changed\n")
                with self.assertRaises(ValueError):
                    self.publish(context)
                self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_proof_and_context_receipt_are_bound_to_the_snapshot(self):
        context = self.prepare()
        request_path = context / "source" / projection.REQUEST
        request = json.loads(request_path.read_bytes())
        request["sourceProof"]["sourceRevision"] = "1" * 40
        request_path.write_bytes(projection.encoded(request))
        with self.assertRaisesRegex(ValueError, "context"):
            self.publish(context)
        self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_installed_dependency_version_is_observed(self):
        context = self.prepare()
        with patch.object(projection.metadata, "version", return_value="0.0.0"):
            with self.assertRaisesRegex(ValueError, "installed-version"):
                self.publish(context)
        self.assertEqual(list((self.root / "output").iterdir()), [])

    def test_output_faults_preserve_complete_prior_output(self):
        context = self.prepare()
        prior = self.publish(context)
        before = tree(prior)
        source, receipt = context / "source", context / "context-receipt.json"
        def corrupt(output):
            projection.produce(output, source, receipt)
            (output / "site/schemas/v2.0/receipt.schema.json").write_bytes(b"{}")
        with self.assertRaises(ValueError):
            self.publish(context, corrupt)
        def fail(output):
            (output / "partial.txt").write_bytes(b"partial")
            raise ValueError("producer-fixture")
        with self.assertRaisesRegex(ValueError, "producer-fixture"):
            self.publish(context, fail)
        def partial(path, content):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"partial")
            raise OSError("write-fixture")
        with patch.object(projection.pages, "_write_text", partial):
            with self.assertRaisesRegex(OSError, "write-fixture"):
                self.publish(context)
        self.assertEqual(tree(prior), before)
        self.assertEqual({p.name for p in prior.parent.iterdir()}, {prior.name})

    def test_output_collision_retains_the_existing_directory(self):
        context = self.prepare()
        output = self.root / "output"
        prior = output / "run-collision"
        prior.mkdir(parents=True)
        (prior / "retained").write_bytes(b"original")
        def allocate(*args, **kwargs):
            path = Path(kwargs["dir"]) / ".pending-collision"
            path.mkdir()
            return str(path)
        original = projection.runtime.tempfile.mkdtemp
        def only_pending(*args, **kwargs):
            return allocate(*args, **kwargs) if kwargs.get("prefix") == ".pending-" else original(*args, **kwargs)
        with patch.object(projection.runtime.tempfile, "mkdtemp", only_pending):
            with self.assertRaisesRegex(ValueError, "fresh-output"):
                self.publish(context)
        self.assertEqual(tree(output), {"run-collision/retained": b"original"})

    def test_preparation_collision_and_interrupted_transfer_preserve_prior_context(self):
        prior = self.prepare()
        before = tree(prior)
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(tree(prior), before)
        with patch.object(projection.os, "rename", side_effect=SystemExit(143)):
            with self.assertRaises(SystemExit):
                self.prepare("interrupted")
        self.assertFalse((self.root / "interrupted").exists())
        self.assertEqual(tree(prior), before)
        self.assertEqual(list(self.root.glob(".projection-*")), [])

    def test_preparation_outer_acquisition_sigterm_and_normal_signal_restoration(self):
        prior = self.prepare()
        before = tree(prior)
        names_before = {path.name for path in self.root.iterdir()}
        code = '''import pathlib, signal, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent / "tests"))
import container_projection as p
from container_patch_fixtures import patch_inputs
source, proof, destination, dependencies = map(pathlib.Path, sys.argv[2:6])
phase = sys.argv[6]
with patch_inputs() as child_patches:
    print("synthetic-patches-bound", flush=True)
    def prior_handler(number, frame):
        raise AssertionError("preparation must use its own termination handler")
    signal.signal(signal.SIGTERM, prior_handler)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1})
    expected_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    allocate = p.tempfile.mkdtemp
    def acquire(*args, **kwargs):
        created = allocate(*args, **kwargs)
        prefix = kwargs.get("prefix", args[1] if len(args) > 1 else None)
        if prefix == ".projection-" and phase == "termination":
            print("outer-acquired-before-return", flush=True)
            signal.raise_signal(signal.SIGTERM)
            assert signal.SIGTERM in signal.sigpending(), "termination must wait for cleanup ownership"
        return created
    p.tempfile.mkdtemp = acquire
    sys.argv = ["container_projection", str(destination), "--source", str(source),
                "--source-proof", str(proof), "--dependencies", str(dependencies),
                "--patches", str(child_patches), "--architecture", "arm64"]
    try:
        status = p.main()
    except SystemExit as error:
        status = error.code
    assert signal.getsignal(signal.SIGTERM) is prior_handler, "handler was not restored"
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == expected_mask, "mask was not restored"
    assert signal.SIGTERM not in signal.sigpending(), "termination was not delivered"
    assert status == (143 if phase == "termination" else 0), f"unexpected preparation result: phase={phase}, status={status}"
    print("signal-state-restored", flush=True)
raise SystemExit(status)
'''
        for phase, status in (("termination", 143), ("normal", 0)):
            with self.subTest(phase=phase):
                destination = self.root / phase
                process = subprocess.run(
                    [sys.executable, "-B", "-c", code, str(ROOT / "infra"),
                     str(self.source), str(self.proof_path), str(destination),
                     str(self.dependencies), phase],
                    capture_output=True, text=True, timeout=10,
                )
                diagnostics = f"stdout:\n{process.stdout[-4000:]}\nstderr:\n{process.stderr[-4000:]}"
                self.assertEqual(process.returncode, status, diagnostics)
                self.assertEqual(process.stderr, "")
                self.assertIn("signal-state-restored", process.stdout)
                if phase == "termination":
                    self.assertIn("outer-acquired-before-return", process.stdout)
                    self.assertNotIn('"prepared"', process.stdout)
                    self.assertFalse(destination.exists())
                    self.assertEqual({path.name for path in self.root.iterdir()}, names_before)
                else:
                    self.assertIn('"prepared"', process.stdout)
                    self.assertEqual(tree(destination), before)
                    self.assertEqual({path.name for path in self.root.iterdir()}, names_before | {phase})
                self.assertEqual(tree(prior), before)
                self.assertEqual(list(self.root.glob(".projection-*")), [])

    def test_preparation_outer_acquisition_error_restores_signal_mask(self):
        prior = self.prepare()
        before = tree(prior)
        original_handler = signal.getsignal(signal.SIGTERM)
        original_mask = signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})
        try:
            with patch.object(projection.tempfile, "TemporaryDirectory",
                              side_effect=OSError("outer-acquisition-fixture")):
                with self.assertRaisesRegex(OSError, "outer-acquisition-fixture"):
                    self.prepare("failed-acquisition")
            self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK, set()),
                             original_mask - {signal.SIGTERM})
            self.assertIs(signal.getsignal(signal.SIGTERM), original_handler)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, original_mask)
        self.assertFalse((self.root / "failed-acquisition").exists())
        self.assertEqual(tree(prior), before)
        self.assertEqual(list(self.root.glob(".projection-*")), [])

    def test_deadline_during_acquisition_records_ownership_before_cleanup(self):
        context = self.prepare()
        prior = self.publish(context)
        before = tree(prior)
        code = '''import pathlib, signal, sys, time
sys.path.insert(0, sys.argv[1])
import container_projection as p
source, receipt, root = map(pathlib.Path, sys.argv[2:5])
phase = sys.argv[5]
p.ROOT = source
p.platform.system = lambda: "Linux"
p.platform.machine = lambda: "aarch64"
publish, produce, validate = p.runtime.publish, p.produce, p.validate
p.runtime.publish = lambda producer, **options: publish(producer, root, **options)
p.produce = lambda output: produce(output, source, receipt)
p.validate = lambda output: validate(output, source, receipt)
def expire():
    signal.setitimer(signal.ITIMER_REAL, 0.01)
    time.sleep(0.05)
if phase == "preflight":
    admit = p.admit_prepared
    def interrupted_admission(*args):
        print("preflight", flush=True)
        expire()
        return admit(*args)
    p.admit_prepared = interrupted_admission
elif phase in ("acquisition", "termination"):
    allocate = p.runtime.tempfile.mkdtemp
    def interrupted_acquisition(*args, **kwargs):
        created = allocate(*args, **kwargs)
        if kwargs.get("prefix") == ".pending-":
            print("acquired-before-return", flush=True)
            if phase == "termination":
                signal.raise_signal(signal.SIGTERM)
            else:
                expire()
            assert signal.SIGTERM in signal.sigpending(), "termination must wait for ownership"
        return created
    p.runtime.tempfile.mkdtemp = interrupted_acquisition
else:
    write = p.pages._write_text
    def interrupted_write(path, content):
        write(path, content)
        print("partial-written", flush=True)
        expire()
    p.pages._write_text = interrupted_write
p.run_projection()
'''
        for phase, marker, status in (
            ("preflight", "preflight", 124),
            ("acquisition", "acquired-before-return", 124),
            ("partial", "partial-written", 124),
            ("termination", "acquired-before-return", 143),
        ):
            with self.subTest(phase=phase):
                process = subprocess.run(
                    [sys.executable, "-B", "-c", code, str(ROOT / "infra"),
                     str(context / "source"), str(context / "context-receipt.json"),
                     str(prior.parent), phase],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(process.returncode, status, process.stderr)
                self.assertIn(marker, process.stdout)
                self.assertNotIn('"completed"', process.stdout)
                self.assertEqual(tree(prior), before)
                self.assertEqual({p.name for p in prior.parent.iterdir()}, {prior.name})

    def test_real_termination_cleans_partial_projection_and_retains_prior_run(self):
        context = self.prepare()
        prior = self.publish(context)
        before = tree(prior)
        code = '''import pathlib, signal, sys
sys.path.insert(0, sys.argv[1])
import container_projection as p
source, receipt, root = map(pathlib.Path, sys.argv[2:])
original = p.runtime.publish
p.runtime.publish = lambda producer, **options: original(producer, root, **options)
write = p.pages._write_text
def pause(path, content):
    write(path, content)
    print("partial-ready", flush=True)
    signal.pause()
p.pages._write_text = pause
p.runtime.run(lambda out: p.produce(out, source, receipt), validate=lambda out: p.validate(out, source, receipt))
'''
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(ROOT / "infra"),
                                    str(context / "source"), str(context / "context-receipt.json"), str(prior.parent)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertTrue(select.select([process.stdout], [], [], 10)[0], "bounded producer readiness")
            self.assertEqual(process.stdout.readline().strip(), "partial-ready")
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 143, stderr)
            self.assertNotIn('"completed"', stdout)
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
        self.assertEqual(tree(prior), before)
        self.assertEqual({p.name for p in prior.parent.iterdir()}, {prior.name})


if __name__ == "__main__":
    unittest.main()
