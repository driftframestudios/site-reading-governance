#!/usr/bin/env python3
"""Check authored guidance for target-state and replacement-state language."""

from __future__ import annotations

import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".yml", ".yaml"}
PROHIBITION = re.compile(
    r"\b(?:do\s+not|don't|must\s+not|should\s+not|avoid|never)\b",
    re.IGNORECASE,
)
BOUNDARY = re.compile(r"\b(?:SAFETY|PRIVACY)\s+BOUNDARY\b", re.IGNORECASE)
REPLACEMENT = re.compile(
    r"\b(?:replacement|instead|stays|routes?\s+to|stored?\s+in|use\s+the)\b",
    re.IGNORECASE,
)
IDENTIFIER = re.compile(
    r"\b(?:dont|do_not|must_not|should_not|never|avoid)_[A-Za-z0-9_]*\b"
)
EXCLUDED_PARTS = {".git", "__pycache__"}
DIAGNOSTIC_GUIDE = Path("docs/NEGATION_AWARE_LANGUAGE.md")
EXTERNAL_IDENTIFIERS = {"do_not_enforce_on_create"}


@dataclass(frozen=True)
class Finding:
    file: Path
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.message}"


def repository_files() -> Iterable[Path]:
    """Yield authored surfaces in stable path order."""
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and EXCLUDED_PARTS.isdisjoint(path.parts):
            if path.suffix in TEXT_SUFFIXES or path.suffix == ".py":
                yield path


def check_text(path: Path) -> list[Finding]:
    """Find fragile imperative negation and require replacement at hard edges."""
    findings: list[Finding] = []
    relative = path.relative_to(ROOT)
    lines = path.read_text(encoding="utf-8").splitlines()
    fenced = False
    for number, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            fenced = not fenced
        if relative == DIAGNOSTIC_GUIDE and fenced:
            continue
        authored_line = line
        for external_identifier in EXTERNAL_IDENTIFIERS:
            authored_line = authored_line.replace(external_identifier, "")
        if IDENTIFIER.search(authored_line):
            findings.append(
                Finding(relative, number, "identifier should name the desired capability")
            )
        if PROHIBITION.search(authored_line):
            paired_boundary = (
                BOUNDARY.search(authored_line) and REPLACEMENT.search(authored_line)
            )
            if not paired_boundary:
                findings.append(
                    Finding(
                        relative,
                        number,
                        "instruction should lead with a verifiable target state; "
                        "hard boundaries include replacement behavior",
                    )
                )
    return findings


def check_python(path: Path) -> list[Finding]:
    """Inspect comments and identifiers while preserving executable operators."""
    findings: list[Finding] = []
    relative = path.relative_to(ROOT)
    with path.open("rb") as handle:
        tokens = tokenize.tokenize(handle.readline)
        try:
            for token in tokens:
                if token.type == tokenize.COMMENT and PROHIBITION.search(token.string):
                    paired_boundary = (
                        BOUNDARY.search(token.string)
                        and REPLACEMENT.search(token.string)
                    )
                    if not paired_boundary:
                        findings.append(
                            Finding(
                                relative,
                                token.start[0],
                                "comment should state the target invariant",
                            )
                        )
                if token.type == tokenize.NAME and IDENTIFIER.fullmatch(token.string):
                    findings.append(
                        Finding(
                            relative,
                            token.start[0],
                            "identifier should name the desired capability",
                        )
                    )
        except tokenize.TokenError as exc:
            findings.append(Finding(relative, 1, f"Python tokenization failed: {exc}"))
    return findings


def report(findings: Iterable[Finding]) -> int:
    materialized = list(findings)
    if materialized:
        print("Language check found target-state opportunities:")
        for finding in materialized:
            print(f"  - {finding}")
        return 1
    print("Negation-aware language check passed.")
    return 0


def main() -> int:
    findings: list[Finding] = []
    for path in repository_files():
        if path.suffix == ".py":
            findings.extend(check_python(path))
        else:
            findings.extend(check_text(path))
    return report(findings)


if __name__ == "__main__":
    raise SystemExit(main())
