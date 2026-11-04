"""Optional pytest cases for the shared qualifier's report and process contracts."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

import qualify


ROW = {"Line": 1, "Check": "SiteReading.TargetState", "Severity": "warning"}
SECOND = {"Line": 2, "Check": "SiteReading.AmbiguousReferent", "Severity": "suggestion"}
EXPECTED = {
    "a.md": [(1, "SiteReading.TargetState", "warning")] * 2,
    "b.md": [(1, "SiteReading.TargetState", "warning"), (2, "SiteReading.AmbiguousReferent", "suggestion")],
}


def test_authored_expectation_also_requires_a_positive_integer_line():
    expected = {"a.md": [(True, "SiteReading.TargetState", "warning")]}
    with pytest.raises(ValueError, match="positive integers"):
        qualify.check_report(json.dumps({"a.md": [ROW]}).encode(), expected)


def test_reordered_report_keeps_fixture_membership_and_repeated_matches():
    report = {"b.md": [SECOND, ROW], "a.md": [ROW, dict(ROW, Message="Review this occurrence.")]}
    qualify.check_report(json.dumps(report).encode(), EXPECTED)


@pytest.mark.parametrize(("a_rows", "reason"), [
    pytest.param([ROW], "missing", id="one-of-two-identical-hits-lost"),
    pytest.param([ROW, ROW, ROW], "unexpected findings 1", id="extra-hit"),
    pytest.param([ROW, dict(ROW, Line=True)], "positive integers", id="true-compares-equal-to-one"),
    pytest.param([ROW, dict(ROW, Line=1.0)], "positive integers", id="float-compares-equal-to-one"),
    pytest.param([ROW, dict(ROW, Line=0)], "positive integers", id="zero-is-outside-source"),
    pytest.param([ROW, dict(ROW, Check=[])], "named Vale rule", id="structured-rule-name"),
    pytest.param([ROW, {"Line": 1, "Check": "SiteReading.TargetState"}], "Vale severity", id="missing-severity"),
    pytest.param([ROW, []], "finding object", id="non-object-row"),
    pytest.param({}, "array of Vale findings", id="non-array-fixture"),
])
def test_changed_or_malformed_finding_cannot_match(a_rows, reason):
    report = {"a.md": a_rows, "b.md": [ROW, SECOND]}
    with pytest.raises(ValueError, match=reason):
        qualify.check_report(json.dumps(report).encode(), EXPECTED)


@pytest.mark.parametrize("constant", [float("nan"), float("inf")], ids=["NaN", "Infinity"])
def test_non_json_number_in_display_metadata_invalidates_an_otherwise_matching_report(constant):
    report = {"a.md": [ROW, dict(ROW, Confidence=constant)], "b.md": [ROW, SECOND]}
    with pytest.raises(ValueError, match="JSON numbers"):
        qualify.check_report(json.dumps(report).encode(), EXPECTED)


@pytest.mark.parametrize(("raw", "reason"), [
    pytest.param(b"{}", "exactly the named fixtures", id="empty-report"),
    pytest.param(b'{"a.md":[],"c.md":[]}', "exactly the named fixtures", id="wrong-file"),
    pytest.param(b'{"a.md":[],"a.md":[],"b.md":[]}', "repeated JSON field", id="duplicate-file"),
    pytest.param(b'{"a.md":', "UTF-8 JSON", id="truncated-json"),
    pytest.param(b'\xff', "UTF-8 JSON", id="invalid-encoding"),
])
def test_ambiguous_or_incomplete_report_cannot_qualify(raw, reason):
    with pytest.raises(ValueError, match=reason):
        qualify.check_report(raw, EXPECTED)


@pytest.mark.parametrize(("stage", "condition", "message"), [
    ("version", "missing", "version check could not start"),
    ("version", "wrong-version", "requires vale version 3.15.2"),
    ("version", "hang", "version check timed out"),
    ("report", "missing", "fixture run could not start"),
    ("report", "hang", "fixture run timed out"),
    ("report", "exit", "fixture run failed \\(status 3\\)"),
    ("report", "empty", "exactly the named fixtures"),
])
def test_incomplete_process_stops_qualification(tmp_path, monkeypatch, stage, condition, message):
    # Replace only the executable, keeping the production subprocess and cleanup path.
    real_run = subprocess.run
    inputs = []

    def launch(command, **kwargs):
        if command[1] == "--version" and stage == "report":
            return subprocess.CompletedProcess(command, 0, stdout=b"vale version 3.15.2\n")
        if stage == "report":
            inputs.extend(Path(arg) for arg in command[4:])
            assert inputs and all(path.is_file() for path in inputs)
        if condition == "missing":
            return real_run([str(tmp_path / "unavailable-vale")], **kwargs)
        program = {
            "hang": "import time; time.sleep(8)",
            "exit": "raise SystemExit(3)",
            "wrong-version": "print('vale version 3.15.1')",
            "empty": "print('{}')",
        }[condition]
        return real_run([sys.executable, "-c", program], **kwargs)

    monkeypatch.setattr(qualify.subprocess, "run", launch)
    if condition == "hang":
        monkeypatch.setattr(qualify, "PROCESS_TIMEOUT_SECONDS", 0.2)
    config = Path(__file__).resolve().parents[1] / ".vale.ini"
    with pytest.raises(SystemExit, match=message):
        qualify.qualify(config, qualify.SHARED_CASES)
    assert all(not path.exists() for path in inputs)
