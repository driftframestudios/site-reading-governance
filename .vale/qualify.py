"""Exercise a checked-in Vale profile with the pinned executable and synthetic prose."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


VERSION = "vale version 3.15.2"
SHARED_CASES = {
    "instructions.md": (
        "Never release an unverified result.\n\n"
        "Never release an unverified result. Send it to the designated reviewer.\n\n"
        "Never release an unverified result. The recovery path is documented somewhere.\n\n"
        "This is obviously fragile.\n\n"
        "The team reviews labels, dates, times, quantities, units, and owners.\n\n"
        "> Never release an unverified result.\n\n"
        "`Never release an unverified result.`\n\n"
        "```text\nNever release an unverified result.\n```\n\n"
        "A sealed specimen never leaves the rack during this check.\n\n"
        "Never release an unverified result, send it for review instead.\n",
        [
            (1, "SiteReading.TargetState", "warning"),
            (5, "SiteReading.TargetState", "warning"),
            (7, "SiteReading.AmbiguousReferent", "suggestion"),
            (7, "SiteReading.EvidenceGrounding", "suggestion"),
            (9, "SiteReading.SentenceComplexity", "suggestion"),
        ],
    ),
    "procedure.md": (
        "Never discard the plate during the transfer.\n\n"
        "Never discard the plate\nduring the transfer.\n\n"
        "- Never discard the plate.\n"
        "- Never discard the plate\n  during the transfer.\n"
        "- Never discard the plate.\n  Place it on the return rack.\n\n"
        "1. Never discard the plate.\n"
        "2. Keep the plate on the return rack.\n\n"
        "> - Never discard the plate.\n\n"
        "- `Never discard the plate.`\n\n"
        "- Never discard the plate,\n  unless the reviewer records a reason.\n"
        "- Never discard the plate. The recovery\n  path is documented elsewhere.\n",
        [
            (1, "SiteReading.TargetState", "warning"),
            (3, "SiteReading.TargetState", "warning"),
            (6, "SiteReading.TargetState", "warning"),
            (7, "SiteReading.TargetState", "warning"),
            (12, "SiteReading.TargetState", "warning"),
            (21, "SiteReading.TargetState", "warning"),
        ],
    ),
    "instructions.py": (
        "# Never release an unverified result.\n\n"
        'example = "Never release an unverified result."\n\n'
        "def hold():\n"
        '    """Never release an unverified result."""\n',
        [
            (1, "SiteReading.TargetState", "warning"),
            (6, "SiteReading.TargetState", "warning"),
        ],
    ),
}


Finding = tuple[int, str, str]
PROCESS_TIMEOUT_SECONDS = 10


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Vale report contains a repeated JSON field.")
    return fields


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"Expected JSON numbers in the Vale report, received {value}.")


def _finding(line: object, rule: object, severity: object) -> Finding:
    if type(line) is not int or line < 1:
        raise ValueError("Vale source lines must be positive integers.")
    if not isinstance(rule, str) or not rule.strip():
        raise ValueError("Expected a named Vale rule.")
    if not isinstance(severity, str) or severity not in ("suggestion", "warning", "error"):
        raise ValueError("Expected a Vale severity.")
    return line, rule, severity


def finding_counts(rows: object) -> Counter[Finding]:
    """Count comparable findings. Ignore display order and explanatory metadata.

    >>> warning = {"Line": 1, "Check": "SiteReading.TargetState", "Severity": "warning"}
    >>> count = finding_counts([warning, dict(warning, Message="Check the action.")])
    >>> count == {(1, "SiteReading.TargetState", "warning"): 2}
    True
    >>> finding_counts([dict(warning, Line=True)])
    Traceback (most recent call last):
    ...
    ValueError: Vale source lines must be positive integers.
    """
    if not isinstance(rows, list):
        raise ValueError("Expected an array of Vale findings for each fixture.")
    counts: Counter[Finding] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected a Vale finding object.")
        key = _finding(row.get("Line"), row.get("Check"), row.get("Severity"))
        counts[key] += 1
    return counts


def check_report(output: bytes, expected_by_path: dict[str, list[Finding]]) -> None:
    """Check fixture membership and each independently authored expectation."""
    try:
        report = json.loads(
            output.decode("utf-8"), object_pairs_hook=_unique_fields, parse_constant=_reject_nonfinite
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Expected a UTF-8 JSON report from Vale.") from exc
    if not isinstance(report, dict) or report.keys() != expected_by_path.keys():
        raise ValueError("Vale must report findings for exactly the named fixtures.")
    for filename, expected in expected_by_path.items():
        required = Counter(_finding(*finding) for finding in expected)
        observed = finding_counts(report[filename])
        if observed != required:
            missing = dict(required - observed)
            extra = observed - required
            raise ValueError(
                f"{Path(filename).name}: missing {missing!r}, unexpected findings {sum(extra.values())}."
            )


def _run_vale(arguments: list[str], cwd: Path, phase: str) -> bytes:
    try:
        result = subprocess.run(
            ["vale", *arguments], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"Vale {phase} timed out. Check the pinned executable before retrying.") from exc
    except OSError as exc:
        raise SystemExit(f"Vale {phase} could not start. Check {VERSION} on PATH.") from exc
    if result.returncode:
        raise SystemExit(f"Vale {phase} failed (status {result.returncode}).")
    return result.stdout


def qualify(config: Path, cases: dict[str, tuple[str, list[Finding]]]) -> None:
    """Compare every emitted line, rule and severity to the authored expectations."""
    config = config.resolve(strict=True)
    if not cases or not all(expected for _, expected in cases.values()):
        raise SystemExit("Each fixture needs a positive control alongside its protected examples.")

    version = _run_vale(["--version"], config.parent, "version check")
    if version.strip() != VERSION.encode("ascii"):
        raise SystemExit(f"Qualification requires {VERSION} on PATH.")

    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        expected_by_path = {}
        for name, (source, expected) in cases.items():
            if name in {"", ".", ".."} or Path(name).name != name:
                raise ValueError("Fixture names must be plain filenames.")
            path = root / name
            path.write_text(source, encoding="utf-8")
            expected_by_path[str(path)] = expected
        output = _run_vale(
            [f"--config={config}", "--no-global", "--output=JSON", *expected_by_path],
            config.parent, "fixture run",
        )
        try:
            check_report(output, expected_by_path)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    qualify(Path(__file__).resolve().parents[1] / ".vale.ini", SHARED_CASES)
    print("Qualified shared author feedback on the synthetic Markdown and Python fixtures.")
