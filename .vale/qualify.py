"""Exercise a checked-in Vale profile with the pinned executable and synthetic prose."""

from __future__ import annotations

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


def qualify(config: Path, cases: dict[str, tuple[str, list[tuple[int, str, str]]]]) -> None:
    """Compare every emitted line, rule and severity to the authored expectations."""
    config = config.resolve(strict=True)
    if not cases or not all(expected for _, expected in cases.values()):
        raise SystemExit("Each fixture needs a positive control alongside its protected examples.")

    try:
        version = subprocess.check_output(["vale", "--version"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Qualification requires {VERSION} on PATH.") from exc
    if version != VERSION:
        raise SystemExit(f"Qualification requires {VERSION} on PATH.")

    with TemporaryDirectory() as directory:
        expected_by_path = {}
        for name, (source, expected) in cases.items():
            if name in {"", ".", ".."} or Path(name).name != name:
                raise ValueError("Fixture names must be plain filenames.")
            path = Path(directory).resolve() / name
            path.write_text(source, encoding="utf-8")
            expected_by_path[str(path)] = sorted(expected)

        command = [
            "vale",
            f"--config={config}",
            "--no-global",
            "--output=JSON",
            *expected_by_path,
        ]
        result = subprocess.run(command, cwd=config.parent, text=True, capture_output=True)
        if result.returncode:
            raise SystemExit(f"Vale execution failed (status {result.returncode}).")
        try:
            report = json.loads(result.stdout)
            if not isinstance(report, dict) or set(report) != set(expected_by_path):
                raise ValueError("Expected findings for every named fixture.")
            for filename, expected in expected_by_path.items():
                actual = sorted(
                    (row["Line"], row["Check"], row["Severity"]) for row in report[filename]
                )
                if actual != expected:
                    raise SystemExit(f"{Path(filename).name}: expected {expected!r}, observed {actual!r}.")
        except (TypeError, KeyError, ValueError) as exc:
            raise SystemExit("Vale did not return the expected fixture report.") from exc


if __name__ == "__main__":
    qualify(Path(__file__).resolve().parents[1] / ".vale.ini", SHARED_CASES)
    print("Qualified shared author feedback on the synthetic Markdown and Python fixtures.")
