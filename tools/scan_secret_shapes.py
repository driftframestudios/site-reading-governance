#!/usr/bin/env python3
"""Find provider-specific and assignment-shaped secrets without rendering values."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".env",
    ".ini",
    ".json",
    ".md",
    ".properties",
    ".py",
    ".sh",
    ".tf",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {
    ".gitignore",
    "CODEOWNERS",
    "Dockerfile",
    "Makefile",
}
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".terraform",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
SAFE_REFERENCE_PREFIXES = (
    "${",
    "{{",
    "<redacted",
    "<secret",
    "arn:aws:ssm:",
    "arn:aws:secretsmanager:",
    "evidence://",
    "governed://",
    "redacted",
    "secretsmanager://",
    "ssm://",
)


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    redacted_length: int

    def __str__(self) -> str:
        return (
            f"{self.path}:{self.line}: {self.rule} secret-shaped value "
            f"redacted (length {self.redacted_length})"
        )


PRIVATE_KEY_PATTERN = re.compile(
    re.escape("-----BEGIN ")
    + r"(?:RSA |EC |OPENSSH |DSA |PGP )?"
    + re.escape("PRIVATE KEY-----")
)
GENERIC_ASSIGNMENT = re.compile(
    r"""(?ix)
    \b(?:api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|
    client[_-]?secret|password|passwd|private[_-]?key|
    aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key|
    aws[_-]?session[_-]?token)\b
    \s*[:=]\s*
    (?:
      ["'](?P<quoted>[^"'\r\n]{8,})["']
      |
      (?P<bare>[^\s#,'"}]{8,})
    )
    """
)
RULES = (
    Rule("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    Rule(
        "github-token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|"
            r"github_pat_[A-Za-z0-9_]{22,})\b"
        ),
    ),
    Rule("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    Rule("stripe-key", re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    Rule("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    Rule("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b")),
    Rule(
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
            r"\.[A-Za-z0-9_-]{8,}\b"
        ),
    ),
    Rule(
        "credential-url",
        re.compile(
            r"\b(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)"
            r"://(?P<credential>[^/@\s:]+:[^/@\s]+)@"
        ),
    ),
    Rule(
        "bearer-token",
        re.compile(r"(?i)\bbearer\s+(?P<bearer>[A-Za-z0-9._~+/-]{12,}=*)"),
    ),
    Rule("private-key", PRIVATE_KEY_PATTERN),
    Rule("generic-secret-assignment", GENERIC_ASSIGNMENT),
)


def repository_files(root: Path) -> Iterable[Path]:
    """Yield authored text surfaces in stable order."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not EXCLUDED_PARTS.isdisjoint(path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            yield path


def _secret_text(match: re.Match[str]) -> str:
    groups = match.groupdict()
    for name in ("quoted", "bare", "credential", "bearer"):
        value = groups.get(name)
        if value is not None:
            return value
    return match.group(0)


def _is_reference(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized.startswith(SAFE_REFERENCE_PREFIXES)


def scan_text(path: Path, text: str, display_path: Path | None = None) -> list[Finding]:
    """Return masked metadata for secret-shaped values in one text surface."""
    findings: list[Finding] = []
    rendered_path = display_path or path
    seen: set[tuple[int, str]] = set()
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            secret = _secret_text(match)
            if _is_reference(secret):
                continue
            marker = (match.start(), rule.name)
            if marker in seen:
                continue
            seen.add(marker)
            findings.append(
                Finding(
                    path=rendered_path,
                    line=text.count("\n", 0, match.start()) + 1,
                    rule=rule.name,
                    redacted_length=len(secret),
                )
            )
    return findings


def scan_repository(root: Path = ROOT) -> list[Finding]:
    """Scan UTF-8 text files while preserving secret values outside output."""
    findings: list[Finding] = []
    resolved_root = root.resolve()
    for path in repository_files(resolved_root):
        try:
            content = path.read_bytes()
            if b"\x00" in content:
                continue
            text = content.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_text(path, text, path.relative_to(resolved_root)))
    return findings


def report(findings: Iterable[Finding]) -> int:
    materialized = list(findings)
    if materialized:
        print("Secret-shape scan found protected-value candidates:")
        for finding in materialized:
            print(f"  - {finding}")
        return 1
    print("Secret-shape scan passed.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return report(scan_repository(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
