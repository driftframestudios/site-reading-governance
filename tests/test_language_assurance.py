"""Golden-corpus and contract tests for deterministic language assurance."""

from __future__ import annotations

import datetime as dt
from hashlib import sha256
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_tool():
    path = ROOT / "tools" / "check_language.py"
    spec = importlib.util.spec_from_file_location("language_assurance", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["language_assurance"] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


language = load_tool()
CORPUS = json.loads(
    (ROOT / "language-policy" / "corpus-v1.json").read_text(encoding="utf-8")
)
FIXED_NOW = dt.datetime(2026, 7, 29, tzinfo=dt.timezone.utc)
EXPECTED_MANIFEST_SHA256 = (
    "95087f281455c45608981152948f8909e74528706662625b6e8a4da9e5182a96"
)


def observed_finding(finding) -> dict[str, object]:
    return {
        "rule_id": finding.rule_id,
        "severity": finding.severity,
        "surface_kind": finding.surface_kind,
        "start_line": finding.start_line,
        "end_line": finding.end_line,
        "fingerprint": finding.fingerprint,
    }


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def case_exemptions(case: dict[str, object]) -> list[object]:
    return [
        language.Exemption(
            exemption_id=item["exemption_id"],
            rule_id=item["rule_id"],
            path=item["path"],
            fingerprint=item["fingerprint"],
            rationale=item["rationale"],
            owner_role=item["owner_role"],
            reviewed_at=parse_utc(item["reviewed_at"]),
            expires_at=parse_utc(item["expires_at"]),
        )
        for item in case.get("case_exemptions", [])
    ]


class LanguageAssuranceTests(unittest.TestCase):
    def test_policy_release_and_rule_ids_are_stable(self) -> None:
        self.assertEqual("language-policy-v1.0.0", language.POLICY_RELEASE)
        self.assertEqual(
            {
                "LANG001_UNPAIRED_PROHIBITION",
                "LANG002_NEGATIVE_IDENTIFIER",
                "LANG003_UNVERIFIABLE_TARGET",
                "LANG900_PARSE_FAILURE",
                "LANG901_EXEMPTION_INVALID",
            },
            set(language.RULES),
        )

    def test_manifest_and_corpus_are_canonical_and_digest_pinned(self) -> None:
        manifest_path = ROOT / "language-policy" / "manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        self.assertEqual(
            EXPECTED_MANIFEST_SHA256,
            sha256(manifest_bytes).hexdigest(),
        )
        self.assertEqual(
            (
                json.dumps(
                    manifest,
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
            manifest_bytes,
        )
        self.assertEqual(
            {
                "assets",
                "diagnostic_reason_codes",
                "exemption_contract",
                "exit_contract",
                "fingerprint_contract",
                "format_aliases",
                "manifest_version",
                "output_schema_version",
                "policy_release",
                "rules",
                "supported_formats",
                "surface_kinds",
            },
            set(manifest),
        )
        self.assertEqual(language.POLICY_RELEASE, manifest["policy_release"])
        self.assertEqual(
            language.OUTPUT_SCHEMA_VERSION,
            manifest["output_schema_version"],
        )
        self.assertIn("case-preserving", manifest["fingerprint_contract"])
        self.assertIn("policy_release omitted", manifest["fingerprint_contract"])
        self.assertEqual(language.RULES, manifest["rules"])
        self.assertEqual(
            sorted(language.DIAGNOSTIC_REASON_MESSAGES),
            manifest["diagnostic_reason_codes"],
        )
        self.assertEqual(
            ["json", "markdown", "python", "yaml"],
            manifest["supported_formats"],
        )
        self.assertEqual(
            {
                "md": "markdown",
                "py": "python",
                "yml": "yaml",
            },
            manifest["format_aliases"],
        )
        self.assertEqual(
            sorted(language.SURFACE_KINDS),
            manifest["surface_kinds"],
        )
        self.assertEqual(
            {
                "0": "no_active_findings",
                "1": "actionable_policy_findings",
                "2": "parse_or_exemption_integrity_failure",
            },
            manifest["exit_contract"],
        )
        self.assertEqual(
            {
                "applied_receipts": "retained_in_text_json_sarif",
                "exact_match_dimensions": "rule_id + path + fingerprint",
                "match_multiplicity": "exactly_one_current_occurrence",
                "registry_application": "all_or_nothing_fail_closed",
            },
            manifest["exemption_contract"],
        )

        expected_mappings = {
            "language-policy-core": (
                "tools/language_policy_core.py",
                "scripts/language_policy_core.py",
            ),
            "language-policy-qualification-corpus": (
                "language-policy/corpus-v1.json",
                "language-policy/corpus-v1.json",
            ),
        }
        self.assertEqual(
            set(expected_mappings),
            {item["asset_id"] for item in manifest["assets"]},
        )
        for asset in manifest["assets"]:
            self.assertEqual(
                {
                    "asset_id",
                    "governance_path",
                    "projection_path",
                    "sha256",
                },
                set(asset),
            )
            self.assertEqual(
                expected_mappings[asset["asset_id"]],
                (asset["governance_path"], asset["projection_path"]),
            )
            content = (ROOT / asset["governance_path"]).read_bytes()
            self.assertEqual(
                f"sha256:{sha256(content).hexdigest()}",
                asset["sha256"],
            )

        corpus_path = ROOT / "language-policy" / "corpus-v1.json"
        corpus_bytes = corpus_path.read_bytes()
        self.assertEqual(
            (
                json.dumps(
                    json.loads(corpus_bytes),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n"
            ).encode("utf-8"),
            corpus_bytes,
        )
        case_ids = [case["case_id"] for case in CORPUS["cases"]]
        self.assertEqual(sorted(case_ids), case_ids)

    def test_compatibility_api_is_exposed_by_the_repository_wrapper(self) -> None:
        for name in (
            "check_content",
            "check_repository",
            "load_exemptions",
            "apply_exemptions",
            "text_report",
            "json_report",
            "sarif_report",
            "exit_code",
        ):
            self.assertTrue(callable(getattr(language, name)))
        findings = language.check_content(
            "fixtures/compatibility.md",
            "Never publish an unsigned compatibility result.",
            format_hint="markdown",
        )
        self.assertEqual(1, language.exit_code(findings))
        self.assertIn(language.POLICY_RELEASE, language.text_report(findings))
        self.assertEqual(
            language.OUTPUT_SCHEMA_VERSION,
            json.loads(language.json_report(findings))["schema_version"],
        )
        self.assertEqual(
            "2.1.0",
            json.loads(language.sarif_report(findings))["version"],
        )
        result = language.scan_content(
            "fixtures/compatibility.md",
            "Never publish an unsigned compatibility result.",
            "markdown",
            report_unused=False,
        )
        self.assertEqual(list(result.findings), list(result))
        self.assertEqual(len(result.findings), len(result))
        self.assertEqual(result.findings[0], result[0])
        self.assertEqual(result.findings, result[:])
        extended: list[object] = []
        extended.extend(result)
        self.assertEqual(list(result.findings), extended)
        self.assertTrue(result)
        self.assertFalse(language.ScanResult(()))

    def test_golden_corpus_has_exact_behavior(self) -> None:
        self.assertEqual(language.POLICY_RELEASE, CORPUS["policy_release"])
        self.assertGreaterEqual(len(CORPUS["cases"]), 50)
        self.assertEqual(
            {
                "should_flag",
                "should_pass",
                "exempt",
                "exemption_invalid",
            },
            {case["expectation"] for case in CORPUS["cases"]},
        )
        seen: set[str] = set()
        for case in CORPUS["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertNotIn(case["case_id"], seen)
                seen.add(case["case_id"])
                result = language.scan_content(
                    path=case["path"],
                    content=case["content"],
                    format_name=case["format"],
                    exemptions=case_exemptions(case),
                    report_unused=True,
                    as_of=FIXED_NOW,
                )
                self.assertEqual(
                    case["expected_findings"],
                    [observed_finding(item) for item in result.findings],
                )
                self.assertEqual(
                    case["expected_exemptions_applied"],
                    [
                        item.exemption_id
                        for item in result.exemptions_applied
                    ],
                )
                if case["expectation"] == "should_flag":
                    self.assertTrue(result.findings)
                elif case["expectation"] == "should_pass":
                    self.assertEqual(0, result.exit_code)
                elif case["expectation"] == "exempt":
                    self.assertEqual(0, result.exit_code)
                    self.assertTrue(result.exemptions_applied)
                else:
                    self.assertEqual("exemption_invalid", case["expectation"])
                    self.assertEqual(2, result.exit_code)
                    self.assertIn(
                        "LANG901_EXEMPTION_INVALID",
                        {item.rule_id for item in result.findings},
                    )

    def test_markdown_surfaces_distinguish_prose_quote_and_example(self) -> None:
        surfaces = language.extract_markdown_surfaces(
            "fixture.md",
            "# Guidance\n\n"
            "Records remain attributable.\n\n"
            "> Operators must not copy this quotation.\n\n"
            "## Diagnostic example\n\n"
            "Operators must not copy this literal.\n",
        )
        kinds = [surface.kind for surface in surfaces]
        self.assertIn("authored_prose", kinds)
        self.assertIn("quote", kinds)
        self.assertIn("example", kinds)
        self.assertFalse(
            next(surface for surface in surfaces if surface.kind == "quote").enforce
        )
        self.assertFalse(
            next(surface for surface in surfaces if surface.kind == "example").enforce
        )

    def test_json_inspects_values_and_preserves_structured_control_context(self) -> None:
        key_only = language.scan_content(
            "fixture.json",
            '{"must_not_publish": true, "instruction": "Records remain attributable."}',
            "json",
            report_unused=False,
        )
        self.assertEqual((), key_only.findings)

        example_content = (
            ROOT / "examples" / "language-control.json"
        ).read_text(encoding="utf-8")
        complete_control = language.scan_content(
            "examples/language-control.json",
            example_content,
            "json",
            report_unused=False,
        )
        self.assertEqual((), complete_control.findings)

    def test_python_reader_inspects_comments_docstrings_and_identifiers(self) -> None:
        result = language.scan_content(
            "fixture.py",
            '"""Records remain attributable and a test verifies the state."""\n'
            "# Operators must not publish the raw record.\n"
            "def avoid_review():\n"
            "    return True\n",
            "python",
            report_unused=False,
        )
        self.assertEqual(
            [
                ("LANG001_UNPAIRED_PROHIBITION", "code_comment"),
                ("LANG002_NEGATIVE_IDENTIFIER", "identifier"),
            ],
            [(item.rule_id, item.surface_kind) for item in result.findings],
        )

    def test_exact_exemption_key_is_required(self) -> None:
        case = next(
            item
            for item in CORPUS["cases"]
            if item["expectation"] == "exempt"
        )
        exemption = dict(case["case_exemptions"][0])
        exemption["path"] = "fixtures/another.md"
        document = {
            "policy_release": language.POLICY_RELEASE,
            "exemptions": [exemption],
        }
        exemptions, issues = language.load_exemptions_text(
            json.dumps(document),
            as_of=FIXED_NOW,
        )
        self.assertEqual([], issues)
        result = language.scan_content(
            case["path"],
            case["content"],
            case["format"],
            exemptions=exemptions,
            report_unused=True,
        )
        self.assertEqual(
            [
                exemption["rule_id"],
                "LANG901_EXEMPTION_INVALID",
            ],
            sorted(item.rule_id for item in result.findings),
        )
        self.assertEqual(2, result.exit_code)

    def test_entire_registry_fails_closed_and_preserves_no_receipts(self) -> None:
        case = next(
            item
            for item in CORPUS["cases"]
            if item["case_id"] == "CANON-WHOLE-REGISTRY-FAIL-CLOSED-001"
        )
        result = language.scan_content(
            case["path"],
            case["content"],
            case["format"],
            exemptions=case_exemptions(case),
            report_unused=True,
            as_of=FIXED_NOW,
        )
        self.assertEqual(2, result.exit_code)
        self.assertEqual((), result.applied_exemptions)
        self.assertEqual(
            {"LANG002_NEGATIVE_IDENTIFIER", "LANG901_EXEMPTION_INVALID"},
            {item.rule_id for item in result.findings},
        )

    def test_direct_exemption_objects_receive_full_registry_validation(self) -> None:
        case_ids = {
            "CANON-FUTURE-REVIEWED-EXEMPTION-001",
            "CANON-OVERLONG-WINDOW-EXEMPTION-001",
            "CANON-REVERSED-WINDOW-EXEMPTION-001",
        }
        for case in (
            item for item in CORPUS["cases"] if item["case_id"] in case_ids
        ):
            with self.subTest(case=case["case_id"]):
                result = language.scan_content(
                    case["path"],
                    case["content"],
                    case["format"],
                    exemptions=case_exemptions(case),
                    as_of=FIXED_NOW,
                )
                self.assertEqual(2, result.exit_code)
                self.assertEqual((), result.applied_exemptions)
                self.assertIn(
                    "LANG901_EXEMPTION_INVALID",
                    {item.rule_id for item in result.findings},
                )

    def test_expired_exemption_is_reported_and_cannot_suppress(self) -> None:
        case = next(
            item
            for item in CORPUS["cases"]
            if item["expectation"] == "exempt"
        )
        exemption = dict(case["case_exemptions"][0])
        exemption["expires_at"] = "2026-07-29T20:00:00Z"
        document = {
            "policy_release": language.POLICY_RELEASE,
            "exemptions": [exemption],
        }
        exemptions, issues = language.load_exemptions_text(
            json.dumps(document),
            as_of=dt.datetime(2026, 7, 30, tzinfo=dt.timezone.utc),
        )
        self.assertEqual([], exemptions)
        self.assertEqual(
            ["LANG901_EXEMPTION_INVALID"],
            [item.rule_id for item in issues],
        )
        result = language.scan_content(
            case["path"],
            case["content"],
            case["format"],
            exemption_issues=issues,
            report_unused=True,
        )
        self.assertEqual(
            [
                exemption["rule_id"],
                "LANG901_EXEMPTION_INVALID",
            ],
            sorted(item.rule_id for item in result.findings),
        )

    def test_overbroad_and_overlong_exemptions_fail_closed(self) -> None:
        case = next(
            item
            for item in CORPUS["cases"]
            if item["expectation"] == "exempt"
        )
        for mutation in ("glob", "window"):
            with self.subTest(mutation=mutation):
                exemption = dict(case["case_exemptions"][0])
                if mutation == "glob":
                    exemption["path"] = "fixtures/*.md"
                else:
                    exemption["expires_at"] = "2027-07-28T20:00:00Z"
                document = {
                    "policy_release": language.POLICY_RELEASE,
                    "exemptions": [exemption],
                }
                exemptions, issues = language.load_exemptions_text(
                    json.dumps(document),
                    as_of=FIXED_NOW,
                )
                self.assertEqual([], exemptions)
                self.assertEqual(
                    ["LANG901_EXEMPTION_INVALID"],
                    [item.rule_id for item in issues],
                )

    def test_unicode_normalization_stabilizes_finding_fingerprint(self) -> None:
        fingerprints = {
            language.scan_content(
                "fixtures/unicode.md",
                text,
                "markdown",
                report_unused=False,
            ).findings[0].fingerprint
            for text in (
                "Operators must not publish José records.",
                "Operators must not publish Jose\u0301 records.",
            )
        }
        self.assertEqual(1, len(fingerprints))

    def test_fingerprint_is_line_stable_case_preserving_and_release_independent(
        self,
    ) -> None:
        base = language.scan_content(
            "fixtures/fingerprint.md",
            "Never publish an unsigned result.",
            "markdown",
            report_unused=False,
        ).findings[0]
        moved = language.scan_content(
            "fixtures/fingerprint.md",
            "\n\nNever publish an unsigned result.",
            "markdown",
            report_unused=False,
        ).findings[0]
        changed_case = language.scan_content(
            "fixtures/fingerprint.md",
            "Never Publish an unsigned result.",
            "markdown",
            report_unused=False,
        ).findings[0]
        self.assertEqual(base.fingerprint, moved.fingerprint)
        self.assertNotEqual(base.fingerprint, changed_case.fingerprint)
        expected = language.finding_fingerprint(
            path=base.path,
            rule_id=base.rule_id,
            surface_kind=base.surface_kind,
            evidence="Never publish an unsigned result.",
        )
        self.assertEqual(base.fingerprint, expected)

    def test_parsers_fail_closed(self) -> None:
        cases = (
            ("fixture.json", '{"value": "first", "value": "second"}', "json"),
            ("fixture.md", "```text\nopen fence", "markdown"),
            ("fixture.yml", 'instruction: "open quote', "yaml"),
            ("fixture.py", "def incomplete(:\n    pass\n", "python"),
        )
        for path, content, format_name in cases:
            with self.subTest(format=format_name):
                result = language.scan_content(
                    path,
                    content,
                    format_name,
                    report_unused=False,
                )
                self.assertEqual(2, result.exit_code)
                self.assertEqual(
                    ["LANG900_PARSE_FAILURE"],
                    [item.rule_id for item in result.findings],
                )

    def test_repository_reader_refuses_out_of_root_paths_and_symlink_targets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            repository = workspace / "repository"
            repository.mkdir()
            outside = workspace / "outside.md"
            outside.write_text(
                "external-content-sentinel",
                encoding="utf-8",
            )
            link = repository / "linked.md"
            link.symlink_to(outside)

            self.assertIn(link, list(language.repository_files(repository)))
            linked_findings = language._read_findings(link, repository)
            self.assertEqual(
                ["LANG900_PARSE_FAILURE"],
                [item.rule_id for item in linked_findings],
            )
            self.assertEqual("linked.md", linked_findings[0].path)
            self.assertNotIn(
                "external-content-sentinel",
                linked_findings[0].message,
            )

            direct_findings = language._read_findings(outside, repository)
            self.assertEqual("<outside-root>", direct_findings[0].path)
            self.assertEqual(
                "LANG900_PARSE_FAILURE",
                direct_findings[0].rule_id,
            )
            self.assertNotIn(
                "external-content-sentinel",
                direct_findings[0].message,
            )

    def test_repository_io_diagnostics_are_portable_across_roots(self) -> None:
        valid_registry = json.dumps(
            {
                "policy_release": language.POLICY_RELEASE,
                "exemptions": [],
            }
        )

        def build_fixture(workspace: Path, label: str):
            repository = workspace / f"repository-{label}"
            policy = repository / "language-policy"
            policy.mkdir(parents=True)
            (policy / "exemptions.json").write_text(
                valid_registry,
                encoding="utf-8",
            )
            unreadable = repository / "unreadable.md"
            unreadable.write_text("Records remain attributable.", encoding="utf-8")
            outside = workspace / f"outside-{label}.md"
            outside.write_text("external-content-sentinel", encoding="utf-8")
            linked = repository / "linked.md"
            linked.symlink_to(outside)
            requested = [
                Path("linked.md"),
                Path("missing.md"),
                Path("unreadable.md"),
                outside,
            ]
            return repository, requested

        original_read_text = Path.read_text

        def bounded_read_text(path: Path, *args, **kwargs):
            if path.name == "unreadable.md":
                raise PermissionError("host-specific unreadable path")
            return original_read_text(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            first_root, first_requested = build_fixture(workspace, "one")
            second_root, second_requested = build_fixture(workspace, "two")
            with mock.patch.object(Path, "read_text", new=bounded_read_text):
                first = language.check_repository(
                    first_root,
                    first_requested,
                    as_of=FIXED_NOW,
                )
                second = language.check_repository(
                    second_root,
                    second_requested,
                    as_of=FIXED_NOW,
                )

            self.assertEqual(
                {
                    "SOURCE_PATH_MISSING",
                    "SOURCE_PATH_OUTSIDE_ROOT",
                    "SOURCE_PATH_SYMLINK",
                    "SOURCE_PATH_UNREADABLE",
                },
                {item.reason_code for item in first.findings},
            )
            renderers = (
                language.render_text,
                language.render_json,
                language.render_sarif,
            )
            for renderer in renderers:
                with self.subTest(renderer=renderer.__name__):
                    first_output = renderer(first)
                    second_output = renderer(second)
                    self.assertEqual(first_output, second_output)
                    for private_value in (
                        str(workspace),
                        str(first_root),
                        str(second_root),
                        "host-specific unreadable path",
                    ):
                        self.assertNotIn(private_value, first_output)
                    if renderer is language.render_sarif:
                        self.assertNotIn("<outside-root>", first_output)
                        sarif_results = json.loads(first_output)["runs"][0][
                            "results"
                        ]
                        outside_finding = next(
                            item
                            for item in first.findings
                            if item.path == "<outside-root>"
                        )
                        outside_result = next(
                            item
                            for item in sarif_results
                            if item["partialFingerprints"][
                                "languagePolicyFingerprint/v1"
                            ]
                            == outside_finding.fingerprint
                        )
                        self.assertNotIn("locations", outside_result)
                    else:
                        self.assertIn("<outside-root>", first_output)

    def test_exemption_registry_io_diagnostics_are_portable_across_roots(
        self,
    ) -> None:
        original_read_text = Path.read_text

        def denied_registry(path: Path, *args, **kwargs):
            if path.name == "exemptions.json":
                raise PermissionError("host-specific registry path")
            return original_read_text(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            scenarios = (
                ("missing", "EXEMPTION_REGISTRY_MISSING"),
                ("outside", "EXEMPTION_REGISTRY_OUTSIDE_ROOT"),
                ("symlink", "EXEMPTION_REGISTRY_SYMLINK"),
                ("unreadable", "EXEMPTION_REGISTRY_UNREADABLE"),
            )
            for scenario, expected_reason in scenarios:
                with self.subTest(scenario=scenario):
                    results = []
                    for label in ("one", "two"):
                        repository = (
                            workspace / scenario / f"repository-{label}"
                        )
                        registry = (
                            repository
                            / "language-policy"
                            / "exemptions.json"
                        )
                        registry.parent.mkdir(parents=True)
                        configured = None
                        if scenario == "unreadable":
                            registry.write_text("{}", encoding="utf-8")
                        elif scenario in {"outside", "symlink"}:
                            outside = (
                                workspace
                                / scenario
                                / f"outside-{label}.json"
                            )
                            outside.write_text("{}", encoding="utf-8")
                            if scenario == "outside":
                                configured = outside
                            else:
                                registry.symlink_to(outside)
                        patcher = (
                            mock.patch.object(
                                Path,
                                "read_text",
                                new=denied_registry,
                            )
                            if scenario == "unreadable"
                            else mock.patch.object(
                                Path,
                                "read_text",
                                new=original_read_text,
                            )
                        )
                        with patcher:
                            results.append(
                                language.scan_paths(
                                    (),
                                    root=repository,
                                    exemptions_path=configured,
                                    as_of=FIXED_NOW,
                                )
                            )

                    first, second = results
                    self.assertEqual(
                        [expected_reason],
                        [item.reason_code for item in first.findings],
                    )
                    for renderer in (
                        language.render_text,
                        language.render_json,
                        language.render_sarif,
                    ):
                        first_output = renderer(first)
                        self.assertEqual(first_output, renderer(second))
                        self.assertNotIn(str(workspace), first_output)
                        self.assertNotIn(
                            "host-specific registry path",
                            first_output,
                        )

    def test_json_and_sarif_outputs_are_machine_readable(self) -> None:
        result = language.scan_content(
            "fixture.md",
            "Operators must not publish raw evidence.",
            "markdown",
            report_unused=False,
        )
        json_output = json.loads(language.render_json(result))
        self.assertEqual(
            {
                "schema_version",
                "policy_release",
                "status",
                "findings",
                "applied_exemptions",
                "summary",
            },
            set(json_output),
        )
        self.assertEqual(language.POLICY_RELEASE, json_output["policy_release"])
        self.assertEqual(
            language.OUTPUT_SCHEMA_VERSION,
            json_output["schema_version"],
        )
        self.assertEqual(1, json_output["summary"]["finding_count"])
        self.assertEqual(1, json_output["summary"]["exit_code"])
        sarif = json.loads(language.render_sarif(result))
        self.assertEqual("2.1.0", sarif["version"])
        sarif_result = sarif["runs"][0]["results"][0]
        self.assertEqual(
            result.findings[0].fingerprint,
            sarif_result["partialFingerprints"][
                "languagePolicyFingerprint/v1"
            ],
        )
        self.assertEqual(
            language.OUTPUT_SCHEMA_VERSION,
            sarif["runs"][0]["properties"]["schemaVersion"],
        )
        encoded_path_result = language.scan_content(
            "docs/a b#c.md",
            "Operators must not publish raw evidence.",
            "markdown",
            report_unused=False,
        )
        encoded_sarif = json.loads(
            language.render_sarif(encoded_path_result)
        )
        artifact_uri = encoded_sarif["runs"][0]["results"][0]["locations"][0][
            "physicalLocation"
        ]["artifactLocation"]["uri"]
        self.assertEqual("docs/a%20b%23c.md", artifact_uri)
        self.assertNotIn("docs/a b#c.md", language.render_sarif(encoded_path_result))

    def test_repository_exemptions_are_valid_and_fully_used(self) -> None:
        result = language.scan_repository(
            ROOT,
            as_of=FIXED_NOW,
        )
        self.assertEqual((), result.findings)


if __name__ == "__main__":
    unittest.main()
