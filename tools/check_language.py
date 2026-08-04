#!/usr/bin/env python3
"""Governance-local wrapper for the canonical language-policy core."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIRECTORY = Path(__file__).resolve().parent
if str(TOOL_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOL_DIRECTORY))

import language_policy_core as _core


for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


def repository_files(root: Path = ROOT) -> Iterable[Path]:
    return _core.repository_files(root)


def _read_findings(path: Path, root: Path = ROOT) -> list[_core.Finding]:
    return _core._read_findings(path, root)


def check_text(path: Path, root: Path = ROOT) -> list[_core.Finding]:
    return _core.check_text(path, root)


def check_python(path: Path, root: Path = ROOT) -> list[_core.Finding]:
    return _core.check_python(path, root)


def scan_paths(
    paths: Iterable[Path],
    root: Path = ROOT,
    exemptions_path: Path | None = None,
    report_unused: bool = True,
    as_of: _core.dt.datetime | None = None,
) -> _core.ScanResult:
    return _core.scan_paths(
        paths,
        root=root,
        exemptions_path=exemptions_path,
        report_unused=report_unused,
        as_of=as_of,
    )


def scan_repository(
    root: Path = ROOT,
    exemptions_path: Path | None = None,
    as_of: _core.dt.datetime | None = None,
) -> _core.ScanResult:
    return _core.scan_repository(
        root,
        exemptions_path=exemptions_path,
        as_of=as_of,
    )


def check_repository(
    root: Path = ROOT,
    selected_paths: Sequence[Path] | None = None,
    *,
    exemptions_path: Path | None = None,
    as_of: _core.dt.datetime | None = None,
) -> _core.ScanResult:
    return _core.check_repository(
        root,
        selected_paths,
        exemptions_path=exemptions_path,
        as_of=as_of,
    )


def main(argv: Sequence[str] | None = None) -> int:
    return _core.main(ROOT, argv)


if __name__ == "__main__":
    raise SystemExit(main())
