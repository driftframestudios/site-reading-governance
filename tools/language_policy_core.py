#!/usr/bin/env python3
"""Repository-independent, deterministic language-assurance policy core."""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
import datetime as dt
from hashlib import sha256
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tokenize
import unicodedata
from typing import Any, Iterable, Iterator, Sequence
from urllib.parse import quote


POLICY_RELEASE = "language-policy-v1.0.0"
OUTPUT_SCHEMA_VERSION = "language-policy-output-v1"
DEFAULT_EXEMPTIONS = Path("language-policy/exemptions.json")
CORPUS_PATH = Path("language-policy/corpus-v1.json")
MANIFEST_PATH = Path("language-policy/manifest.json")
POLICY_META_PATHS = {CORPUS_PATH, DEFAULT_EXEMPTIONS, MANIFEST_PATH}
TEXT_SUFFIXES = {".json", ".md", ".markdown", ".yml", ".yaml"}
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".vale",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
SURFACE_KINDS = {
    "authored_prose",
    "quote",
    "example",
    "code_comment",
    "docstring",
    "identifier",
    "structured_value",
}

RULES = {
    "LANG001_UNPAIRED_PROHIBITION": {
        "severity": "error",
        "message": (
            "Instruction names a prohibition without an affirmative target and "
            "replacement behavior in the same logical paragraph."
        ),
        "help": (
            "Lead with the state to preserve, then name the hard boundary and "
            "the safe behavior collaborators can perform."
        ),
    },
    "LANG002_NEGATIVE_IDENTIFIER": {
        "severity": "error",
        "message": "Identifier names blocked behavior rather than a desired capability.",
        "help": "Name the state or capability the implementation provides.",
    },
    "LANG003_UNVERIFIABLE_TARGET": {
        "severity": "error",
        "message": (
            "High-consequence target or boundary lacks an observable verification "
            "method in the same logical paragraph."
        ),
        "help": "Name the check, evidence, receipt, metric, or review that verifies it.",
    },
    "LANG900_PARSE_FAILURE": {
        "severity": "error",
        "message": "Authored content could not be parsed by the bounded reader.",
        "help": "Repair the source so every applicable surface can be inspected.",
    },
    "LANG901_EXEMPTION_INVALID": {
        "severity": "error",
        "message": "A language-policy exemption is invalid, expired, or unused.",
        "help": "Use a reviewed, exact, time-bounded exemption or remove stale policy.",
    },
}
RULE_UNPAIRED = "LANG001_UNPAIRED_PROHIBITION"
RULE_IDENTIFIER = "LANG002_NEGATIVE_IDENTIFIER"
RULE_TARGET = "LANG003_UNVERIFIABLE_TARGET"
RULE_PARSE = "LANG900_PARSE_FAILURE"
RULE_EXEMPTION = "LANG901_EXEMPTION_INVALID"

PROHIBITION = re.compile(
    r"\b(?:do\s+not|don['’]t|must\s+not|should\s+not|shall\s+not|"
    r"may\s+not|avoid|never|(?:is|are)\s+prohibited|prohibited\s+from)\b",
    re.IGNORECASE,
)
NEGATIVE_IDENTIFIER = re.compile(
    r"^(?:dont|do_not|must_not|should_not|shall_not|may_not|never|avoid)"
    r"(?:_|$)[A-Za-z0-9_]*$",
    re.IGNORECASE,
)
NEGATIVE_IDENTIFIER_IN_VALUE = re.compile(
    r"\b(?:dont|do_not|must_not|should_not|shall_not|may_not|never|avoid)"
    r"(?:_[A-Za-z0-9_]+)+\b",
    re.IGNORECASE,
)
TARGET_LABEL = re.compile(
    r"\b(?:target[ _]state|desired[ _]state|protected[ _]state)\s*:",
    re.IGNORECASE,
)
BOUNDARY_LABEL = re.compile(
    r"\b(?:safety|privacy|security|quality|regulatory|production)\s+boundary\b",
    re.IGNORECASE,
)
HIGH_CONSEQUENCE = re.compile(
    r"\b(?:credential|secret|personal data|patient|regulated|production|"
    r"safety|privacy|security|quality|regulatory|data integrity)\w*\b",
    re.IGNORECASE,
)
REPLACEMENT_LABEL = re.compile(
    r"\b(?:replacement[ _]behavior|safe[ _]path|recovery[ _]path)\b",
    re.IGNORECASE,
)
REPLACEMENT_TRANSITION = re.compile(
    r"\b(?:instead|in its place|as the safe alternative)\b",
    re.IGNORECASE,
)
AFFIRMATIVE_ACTION = re.compile(
    r"\b(?:remain|remains|stay|stays|preserve|preserves|store|stores|"
    r"route|routes|send|sends|record|records|provide|provides|return|returns|"
    r"redact|redacts|retain|retains|quarantine|quarantines|escalate|escalates|"
    r"restore|restores|use|uses)\b",
    re.IGNORECASE,
)
AFFIRMATIVE_ACTION_START = re.compile(
    r"^(?:please\s+)?(?:preserve|store|route|send|record|provide|return|redact|"
    r"retain|quarantine|escalate|restore|use)\b",
    re.IGNORECASE,
)
POSITIVE_CLAUSE = re.compile(
    r"^\s*(?:(?:instead|replacement behavior|target state)\s*[:,]?\s*)?"
    r"(?:the\s+)?(?:use|route|store|keep|return|record|emit|write|preserve|"
    r"validate|require|send|place|retain|carry|resolve|reconcile|encrypt|"
    r"redact|authenticate|authorize|escalate|defer|prefer|select|name|"
    r"describe|state|verify|bind|publish|retrieve|derive|apply|"
    r"credentials?|records?|requests?|responses?|fixtures?|logs?|evidence|"
    r"results?|receipts?|artifacts?|the\s+[A-Za-z][A-Za-z0-9_-]*)\b",
    re.IGNORECASE,
)
EXPLICIT_OBSERVABLE_CHECK = re.compile(
    r"(?:\b(?:verify|verifies|verified|assert|asserts|asserted|check|checks|"
    r"checked|demonstrate|demonstrates|demonstrated|confirm|confirms|"
    r"confirmed|test|tests|tested|scan|scans|scanned|measure|measures|"
    r"measured|validate|validates|validated|compare|compares|compared)\b|"
    r"\b(?:verification|observable check|schema validation|digest comparison|"
    r"status check|count check|threshold check)\s*:)",
    re.IGNORECASE,
)
VAGUE_TARGET = re.compile(
    r"\b(?:appropriately|properly|safely|securely|carefully|responsibly|"
    r"as\s+needed|best\s+practices?|good\s+practice)\b",
    re.IGNORECASE,
)
HISTORICAL_CONTEXT = re.compile(
    r"\b(?:historical|historically|legacy|formerly|previously|earlier|"
    r"at\s+the\s+time|the\s+(?:19|20)\d{2}\s+(?:runbook|policy|system|"
    r"implementation))\b.*\b(?:said|stated|read|recorded|reported|"
    r"described|used|contained|required|prohibited)\b",
    re.IGNORECASE | re.DOTALL,
)
INLINE_CODE = re.compile(r"`[^`\n]+`")
CURLY_DOUBLE_QUOTE = re.compile(r"“[^”\n]*”")
CURLY_SINGLE_QUOTE = re.compile(r"‘[^’\n]*’")
STRAIGHT_DOUBLE_QUOTE = re.compile(r'"(?:\\.|[^"\\\n])*"')
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
RELATION_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "may",
    "must",
    "never",
    "not",
    "of",
    "on",
    "or",
    "shall",
    "should",
    "the",
    "to",
    "with",
}
CONTROL_KEYS = {
    "boundary",
    "constraint",
    "directive",
    "exclusion",
    "explicit_constraint",
    "guard",
    "instruction",
    "policy",
}
TARGET_KEYS = {
    "evidence",
    "expected",
    "permitted_behavior",
    "replacement",
    "replacement_behavior",
    "target",
    "target_state",
    "verification",
}
STRUCTURED_FIELD_ORDER = (
    "boundary",
    "constraint",
    "directive",
    "exclusion",
    "explicit_constraint",
    "guard",
    "instruction",
    "policy",
    "protected_state",
    "target",
    "target_state",
    "expected",
    "permitted_behavior",
    "replacement",
    "replacement_behavior",
    "verification",
    "evidence",
)
EXAMPLE_HEADING = re.compile(
    r"\b(?:example|examples|diagnostic|diagnostics|counterexample|"
    r"counterexamples|historical source|quoted source)\b",
    re.IGNORECASE,
)
MARKDOWN_HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
MARKDOWN_FENCE = re.compile(r"^\s*(```+|~~~+)")
RFC3339_UTC = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:(?:[0-5][0-9]|60)Z$"
)
FINGERPRINT = re.compile(r"^sha256:[a-f0-9]{64}$")
VALID_RULE_EXEMPTIONS = {
    "LANG001_UNPAIRED_PROHIBITION",
    "LANG002_NEGATIVE_IDENTIFIER",
    "LANG003_UNVERIFIABLE_TARGET",
}
DIAGNOSTIC_REASON_MESSAGES = {
    "SOURCE_PATH_MISSING": (
        "Selected source path is absent; select an existing repository-owned file."
    ),
    "SOURCE_PATH_UNREADABLE": (
        "Selected source path could not be read; restore read access and retry."
    ),
    "SOURCE_PATH_SYMLINK": (
        "Selected source path is a symbolic link; select the repository-owned "
        "regular file."
    ),
    "SOURCE_PATH_OUTSIDE_ROOT": (
        "Selected source path resolves beyond the bounded repository root."
    ),
    "SOURCE_PATH_NOT_REGULAR_FILE": (
        "Selected source path is a directory or special file; select an authored "
        "regular file."
    ),
    "SOURCE_PATH_ENCODING_INVALID": (
        "Selected source path requires valid UTF-8 text."
    ),
    "EXEMPTION_REGISTRY_MISSING": (
        "Exemption registry is absent; restore the reviewed repository registry."
    ),
    "EXEMPTION_REGISTRY_UNREADABLE": (
        "Exemption registry could not be read; restore read access and retry."
    ),
    "EXEMPTION_REGISTRY_SYMLINK": (
        "Exemption registry is a symbolic link; select the repository-owned "
        "regular file."
    ),
    "EXEMPTION_REGISTRY_OUTSIDE_ROOT": (
        "Exemption registry resolves beyond the bounded repository root."
    ),
    "EXEMPTION_REGISTRY_NOT_REGULAR_FILE": (
        "Exemption registry is a directory or special file; select the reviewed "
        "regular file."
    ),
    "EXEMPTION_REGISTRY_ENCODING_INVALID": (
        "Exemption registry requires valid UTF-8 text."
    ),
}


class DuplicateKeyError(ValueError):
    """Signal a duplicate key in a policy-bearing JSON document."""


class SurfaceParseError(ValueError):
    """Signal that a bounded content reader could not inspect its full input."""


@dataclass(frozen=True)
class Surface:
    """One policy-bearing logical surface."""

    path: str
    start_line: int
    end_line: int
    kind: str
    text: str
    location: str = ""
    enforce: bool = True

    def __post_init__(self) -> None:
        if self.kind not in SURFACE_KINDS:
            raise ValueError(f"unsupported surface kind {self.kind!r}")

    @property
    def surface_kind(self) -> str:
        return self.kind


@dataclass(frozen=True)
class Finding:
    """One stable policy result."""

    rule_id: str
    severity: str
    surface_kind: str
    path: str
    start_line: int
    end_line: int
    message: str
    fingerprint: str
    location: str = ""
    reason_code: str = ""

    @property
    def file(self) -> Path:
        """Retain the original checker API used by downstream tests."""
        return Path(self.path)

    @property
    def line(self) -> int:
        """Retain the original checker API used by downstream tests."""
        return self.start_line

    def as_dict(self) -> dict[str, Any]:
        document = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "surface_kind": self.surface_kind,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "message": self.message,
            "fingerprint": self.fingerprint,
        }
        if self.reason_code:
            document["reason_code"] = self.reason_code
        return document

    def __str__(self) -> str:
        location = f" ({self.location})" if self.location else ""
        reason = f" reason={self.reason_code}" if self.reason_code else ""
        return (
            f"{self.path}:{self.start_line}:{self.end_line}: "
            f"{self.severity} {self.rule_id} [{self.surface_kind}] "
            f"{self.message}{location}{reason} ({self.fingerprint})"
        )


@dataclass(frozen=True)
class Exemption:
    """One reviewed, exact, time-bounded policy exception."""

    exemption_id: str
    rule_id: str
    path: str
    fingerprint: str
    rationale: str
    owner_role: str
    reviewed_at: dt.datetime
    expires_at: dt.datetime

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.rule_id, self.path, self.fingerprint)


@dataclass(frozen=True)
class AppliedExemption:
    """Evidence that one finding matched one exact reviewed exception."""

    exemption_id: str
    rule_id: str
    path: str
    fingerprint: str
    owner_role: str
    expires_at: str

    def as_dict(self) -> dict[str, str]:
        return {
            "exemption_id": self.exemption_id,
            "rule_id": self.rule_id,
            "path": self.path,
            "fingerprint": self.fingerprint,
            "owner_role": self.owner_role,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True)
class ScanResult:
    """Active findings and the exceptions that were actually exercised."""

    findings: tuple[Finding, ...]
    applied_exemptions: tuple[AppliedExemption, ...] = ()

    @property
    def exemptions_applied(self) -> tuple[AppliedExemption, ...]:
        """Compatibility alias retained for the governance wrapper."""
        return self.applied_exemptions

    def __iter__(self) -> Iterator[Finding]:
        """Preserve findings-sequence iteration for legacy repository callers."""
        return iter(self.findings)

    def __len__(self) -> int:
        """Return the number of active findings."""
        return len(self.findings)

    def __bool__(self) -> bool:
        """Treat a result as truthy exactly when active findings remain."""
        return bool(self.findings)

    def __getitem__(
        self,
        index: int | slice,
    ) -> Finding | tuple[Finding, ...]:
        """Preserve finding indexing and tuple-backed slice semantics."""
        return self.findings[index]

    @property
    def exit_code(self) -> int:
        if any(
            finding.rule_id
            in {"LANG900_PARSE_FAILURE", "LANG901_EXEMPTION_INVALID"}
            for finding in self.findings
        ):
            return 2
        return 1 if self.findings else 0

    def as_dict(self) -> dict[str, Any]:
        severity_counts: dict[str, int] = defaultdict(int)
        rule_counts: dict[str, int] = defaultdict(int)
        for finding in self.findings:
            severity_counts[finding.severity] += 1
            rule_counts[finding.rule_id] += 1
        status = (
            "integrity_failure"
            if self.exit_code == 2
            else "policy_findings"
            if self.findings
            else "pass"
        )
        return {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "policy_release": POLICY_RELEASE,
            "status": status,
            "findings": [finding.as_dict() for finding in self.findings],
            "applied_exemptions": [
                exemption.as_dict() for exemption in self.applied_exemptions
            ],
            "summary": {
                "finding_count": len(self.findings),
                "applied_exemption_count": len(self.applied_exemptions),
                "severity_counts": dict(sorted(severity_counts.items())),
                "rule_counts": dict(sorted(rule_counts.items())),
                "exit_code": self.exit_code,
            },
        }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json_text(content: str) -> Any:
    def finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number {token!r}")
        return value

    return json.loads(
        content,
        object_pairs_hook=_unique_object,
        parse_float=finite_float,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON token {token!r}")
        ),
    )


def _normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def finding_fingerprint(
    *,
    rule_id: str,
    path: str,
    surface_kind: str,
    evidence: str,
) -> str:
    """Bind a rule and exact authored evidence using NFC and preserved case."""
    material = json.dumps(
        {
            "path": path,
            "rule_id": rule_id,
            "surface_kind": surface_kind,
            "evidence": _normalize_text(evidence),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(material).hexdigest()}"


def _make_finding(
    rule_id: str,
    surface: Surface,
    message: str | None = None,
    *,
    evidence: str | None = None,
    reason_code: str = "",
) -> Finding:
    rule = RULES[rule_id]
    return Finding(
        rule_id=rule_id,
        severity=rule["severity"],
        surface_kind=surface.kind,
        path=surface.path,
        start_line=surface.start_line,
        end_line=surface.end_line,
        message=message or rule["message"],
        fingerprint=finding_fingerprint(
            rule_id=rule_id,
            path=surface.path,
            surface_kind=surface.kind,
            evidence=evidence if evidence is not None else surface.text,
        ),
        location=surface.location,
        reason_code=reason_code,
    )


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError:
        return "<outside-root>"


def _path_resolves_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _diagnostic_message(reason_code: str) -> str:
    """Return one stable message for a typed repository I/O failure."""
    return DIAGNOSTIC_REASON_MESSAGES[reason_code]


def _read_repository_text(
    path: Path,
    root: Path,
    *,
    subject: str,
) -> tuple[str | None, str, str | None]:
    """Read one regular UTF-8 file without exposing host-specific diagnostics."""
    if subject not in {"SOURCE_PATH", "EXEMPTION_REGISTRY"}:
        raise ValueError("unsupported repository text subject")
    display = _display_path(path, root)
    if display == "<outside-root>":
        return None, display, f"{subject}_OUTSIDE_ROOT"
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None, display, f"{subject}_MISSING"
    except OSError:
        return None, display, f"{subject}_UNREADABLE"
    if stat.S_ISLNK(metadata.st_mode):
        return None, display, f"{subject}_SYMLINK"
    if not _path_resolves_within(path, root):
        return None, display, f"{subject}_OUTSIDE_ROOT"
    if not stat.S_ISREG(metadata.st_mode):
        return None, display, f"{subject}_NOT_REGULAR_FILE"
    try:
        return path.read_text(encoding="utf-8"), display, None
    except FileNotFoundError:
        return None, display, f"{subject}_MISSING"
    except UnicodeError:
        return None, display, f"{subject}_ENCODING_INVALID"
    except OSError:
        return None, display, f"{subject}_UNREADABLE"


def _line_for_text(
    content: str,
    value: str,
    cursors: dict[str, int],
) -> int:
    encoded = json.dumps(value, ensure_ascii=False)
    start = content.find(encoded, cursors[value])
    if start < 0:
        start = content.find(encoded)
    if start < 0:
        return 1
    cursors[value] = start + len(encoded)
    return content.count("\n", 0, start) + 1


def extract_json_surfaces(path: str, content: str) -> list[Surface]:
    """Inspect JSON string values recursively while leaving keys as structure."""
    try:
        document = _load_json_text(content)
    except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        raise SurfaceParseError(f"JSON parsing failed: {exc}") from exc

    surfaces: list[Surface] = []
    cursors: dict[str, int] = defaultdict(int)

    def labeled_string_values(
        value: Any,
        label: str,
    ) -> list[tuple[str, str]]:
        if isinstance(value, dict):
            return [
                pair
                for child_label, child in value.items()
                for pair in labeled_string_values(
                    child,
                    f"{label}.{child_label}",
                )
            ]
        if isinstance(value, list):
            return [
                pair
                for child in value
                for pair in labeled_string_values(child, label)
            ]
        return [(f"{label}: {value}", value)] if isinstance(value, str) else []

    def walk(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            present_control = CONTROL_KEYS.intersection(value)
            present_target = TARGET_KEYS.intersection(value)
            language_fields = (
                present_control | present_target
                if present_control and present_target
                else set()
            )
            if language_fields:
                ordered_fields = sorted(
                    language_fields,
                    key=lambda key: (
                        STRUCTURED_FIELD_ORDER.index(key)
                        if key in STRUCTURED_FIELD_ORDER
                        else len(STRUCTURED_FIELD_ORDER),
                        key,
                    ),
                )
                grouped = [
                    pair
                    for key in ordered_fields
                    for pair in labeled_string_values(value[key], key)
                ]
                if grouped:
                    located = [
                        (_line_for_text(content, raw, cursors), labeled)
                        for labeled, raw in grouped
                    ]
                    surfaces.append(
                        Surface(
                            path=path,
                            start_line=min(line for line, _ in located),
                            end_line=max(
                                line + text.count("\n")
                                for line, text in located
                            ),
                            kind="structured_value",
                            text="\n".join(
                                labeled for _, labeled in located
                            ),
                            location=pointer or "/",
                        )
                    )
            for key, child in value.items():
                if key in language_fields:
                    continue
                escaped = key.replace("~", "~0").replace("/", "~1")
                walk(child, f"{pointer}/{escaped}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}")
        elif isinstance(value, str):
            line = _line_for_text(content, value, cursors)
            surfaces.append(
                Surface(
                    path=path,
                    start_line=line,
                    end_line=line + value.count("\n"),
                    kind="structured_value",
                    text=value,
                    location=pointer or "/",
                )
            )

    walk(document, "")
    return surfaces


def _markdown_clean(lines: Sequence[str], kind: str) -> str:
    cleaned: list[str] = []
    for line in lines:
        value = line.strip()
        if kind == "quote":
            value = re.sub(r"^>\s?", "", value)
        value = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", value)
        cleaned.append(value)
    return " ".join(item for item in cleaned if item)


def extract_markdown_surfaces(path: str, content: str) -> list[Surface]:
    """Parse Markdown into prose, quotation, and example-level paragraphs."""
    lines = content.splitlines()
    surfaces: list[Surface] = []
    paragraph: list[str] = []
    paragraph_start = 1
    paragraph_kind = "authored_prose"
    example_depth: int | None = None
    fence_marker: str | None = None
    fence_start = 0
    fence_lines: list[str] = []

    def flush(end_line: int) -> None:
        nonlocal paragraph
        if paragraph:
            text = _markdown_clean(paragraph, paragraph_kind)
            if text:
                surfaces.append(
                    Surface(
                        path=path,
                        start_line=paragraph_start,
                        end_line=end_line,
                        kind=paragraph_kind,
                        text=text,
                        enforce=paragraph_kind == "authored_prose",
                    )
                )
            paragraph = []

    for number, line in enumerate(lines, start=1):
        fence_match = MARKDOWN_FENCE.match(line)
        if fence_marker:
            if fence_match and fence_match.group(1).startswith(fence_marker[0]):
                surfaces.append(
                    Surface(
                        path=path,
                        start_line=fence_start,
                        end_line=number,
                        kind="example",
                        text="\n".join(fence_lines),
                        location="fenced-code",
                        enforce=False,
                    )
                )
                fence_marker = None
                fence_lines = []
            else:
                fence_lines.append(line)
            continue

        if fence_match:
            flush(number - 1)
            fence_marker = fence_match.group(1)
            fence_start = number
            continue

        heading = MARKDOWN_HEADING.match(line)
        if heading:
            flush(number - 1)
            level = len(heading.group("marks"))
            if example_depth is not None and level <= example_depth:
                example_depth = None
            title = heading.group("title")
            diagnostic_heading = bool(EXAMPLE_HEADING.search(title))
            if diagnostic_heading:
                example_depth = level
            surfaces.append(
                Surface(
                    path=path,
                    start_line=number,
                    end_line=number,
                    kind="example" if diagnostic_heading else "authored_prose",
                    text=title,
                    enforce=not diagnostic_heading,
                )
            )
            continue

        if not line.strip():
            flush(number - 1)
            continue

        kind = (
            "quote"
            if line.lstrip().startswith(">")
            else "example"
            if example_depth is not None
            else "authored_prose"
        )
        starts_list_item = bool(
            re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line)
        )
        if paragraph and (kind != paragraph_kind or starts_list_item):
            flush(number - 1)
        if not paragraph:
            paragraph_start = number
            paragraph_kind = kind
        paragraph.append(line)

    flush(len(lines))
    if fence_marker:
        raise SurfaceParseError(
            f"Markdown fence opened on line {fence_start} has no closing fence"
        )
    return surfaces


def _yaml_strip_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == "#" and quote is None and (
            index == 0 or value[index - 1].isspace()
        ):
            return value[:index].rstrip()
    if quote is not None:
        raise SurfaceParseError("YAML scalar contains an unterminated quote")
    return value.strip()


def _yaml_scalar_value(value: str) -> str | None:
    value = _yaml_strip_comment(value)
    if not value or value in {"|", "|-", "|+", ">", ">-", ">+"}:
        return None
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    if value.startswith("${{") and value.endswith("}}"):
        return value
    if value[0:1] in {"[", "{"}:
        quoted = re.findall(r"""(["'])(.*?)(?<!\\)\1""", value)
        return " ".join(item[1] for item in quoted) or None
    if value.lower() in {
        "true",
        "false",
        "null",
        "~",
        "yes",
        "no",
        "on",
        "off",
    }:
        return None
    if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", value):
        return None
    return value


def _yaml_value_fragment(line: str) -> tuple[int, str, bool]:
    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    value = stripped
    if value.startswith("- "):
        value = value[2:].lstrip()
    quote: str | None = None
    escaped = False
    colon = -1
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == ":" and quote is None:
            colon = index
            break
    if quote is not None:
        raise SurfaceParseError("YAML line contains an unterminated quote")
    if colon >= 0:
        return indent, value[colon + 1 :].strip(), True
    if stripped.startswith("- "):
        return indent, value, True
    return indent, "", False


def extract_yaml_surfaces(path: str, content: str) -> list[Surface]:
    """Inspect conservative YAML scalar values without treating keys as prose."""
    lines = content.splitlines()
    surfaces: list[Surface] = []
    index = 0
    while index < len(lines):
        number = index + 1
        line = lines[index]
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise SurfaceParseError(
                f"YAML indentation uses a tab on line {number}"
            )
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in {"---", "..."}:
            index += 1
            continue
        indent, fragment, has_value = _yaml_value_fragment(line)
        if not has_value:
            index += 1
            continue
        if fragment in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            block_start = index + 2
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    block.append("")
                    index += 1
                    continue
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                if candidate_indent <= indent:
                    break
                block.append(candidate.strip())
                index += 1
            if not block:
                raise SurfaceParseError(
                    f"YAML block scalar on line {number} has no indented content"
                )
            surfaces.append(
                Surface(
                    path=path,
                    start_line=block_start,
                    end_line=index,
                    kind="structured_value",
                    text=(" " if fragment.startswith(">") else "\n").join(block),
                    location=f"yaml-scalar:{number}",
                )
            )
            continue
        scalar = _yaml_scalar_value(fragment)
        if scalar is not None:
            surfaces.append(
                Surface(
                    path=path,
                    start_line=number,
                    end_line=number,
                    kind="structured_value",
                    text=scalar,
                    location=f"yaml-scalar:{number}",
                )
            )
        index += 1
    return surfaces


def _docstring_nodes(tree: ast.AST) -> Iterable[ast.Constant]:
    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue
        body = getattr(node, "body", [])
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            yield body[0].value


def extract_python_surfaces(path: str, content: str) -> list[Surface]:
    """Inspect Python comments, docstrings, and capability identifiers."""
    try:
        tree = ast.parse(content, filename=path)
    except (SyntaxError, ValueError) as exc:
        raise SurfaceParseError(f"Python parsing failed: {exc}") from exc

    surfaces: list[Surface] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        raise SurfaceParseError(f"Python tokenization failed: {exc}") from exc

    for token in tokens:
        if token.type == tokenize.COMMENT:
            surfaces.append(
                Surface(
                    path=path,
                    start_line=token.start[0],
                    end_line=token.end[0],
                    kind="code_comment",
                    text=token.string.lstrip("#").strip(),
                )
            )
        elif (
            token.type == tokenize.NAME
            and NEGATIVE_IDENTIFIER.fullmatch(token.string)
        ):
            surfaces.append(
                Surface(
                    path=path,
                    start_line=token.start[0],
                    end_line=token.end[0],
                    kind="identifier",
                    text=token.string,
                )
            )

    for node in _docstring_nodes(tree):
        surfaces.append(
            Surface(
                path=path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                kind="docstring",
                text=node.value,
            )
        )
    return sorted(
        surfaces,
        key=lambda item: (item.start_line, item.end_line, item.kind, item.text),
    )


def _scrub_quoted_material(text: str) -> str:
    """Remove inline diagnostic literals before directive evaluation."""
    scrubbed = INLINE_CODE.sub(" ", text)
    scrubbed = CURLY_DOUBLE_QUOTE.sub(" ", scrubbed)
    scrubbed = CURLY_SINGLE_QUOTE.sub(" ", scrubbed)
    return STRAIGHT_DOUBLE_QUOTE.sub(" ", scrubbed)


def _directive_prohibition(text: str) -> re.Match[str] | None:
    """Return a normative prohibition while filtering descriptive ``do not``."""
    for match in PROHIBITION.finditer(text):
        phrase = match.group(0).casefold()
        if phrase != "do not":
            return match
        sentence_prefix = SENTENCE_BOUNDARY.split(text[: match.start()])[-1]
        prefix = sentence_prefix.strip()
        if (
            not prefix
            or prefix.endswith((":", ";", "—"))
            or BOUNDARY_LABEL.search(prefix)
        ):
            return match
    return None


def _clauses_related(exclusion: str, target: str) -> bool:
    target_lower = target.casefold()
    if re.search(
        r"\b(?:it|its|they|their|them|this|that|these|those)\b",
        target_lower,
    ):
        return True
    exclusion_words = {
        word
        for word in re.findall(
            r"[A-Za-z][A-Za-z0-9_-]+",
            exclusion.casefold(),
        )
        if word not in RELATION_STOPWORDS and len(word) > 2
    }
    target_words = {
        word
        for word in re.findall(
            r"[A-Za-z][A-Za-z0-9_-]+",
            target_lower,
        )
        if word not in RELATION_STOPWORDS and len(word) > 2
    }
    return bool(exclusion_words & target_words)


def _replacement_text(
    text: str,
    prohibition: re.Match[str],
) -> str | None:
    """Return one explicit or related replacement following the prohibition."""
    tail = text[prohibition.end() :]
    cue = REPLACEMENT_LABEL.search(tail) or REPLACEMENT_TRANSITION.search(tail)
    if cue:
        return tail[cue.start() :].strip()

    prohibition_sentence = SENTENCE_BOUNDARY.split(
        text[: prohibition.end()]
    )[-1]
    for separator in (";", "—"):
        if separator in tail:
            candidate = tail.split(separator, 1)[1].strip()
            if (
                POSITIVE_CLAUSE.search(candidate)
                and _clauses_related(prohibition_sentence, candidate)
            ):
                return candidate

    sentences = SENTENCE_BOUNDARY.split(text)
    source_index = next(
        (
            index
            for index, sentence in enumerate(sentences)
            if _directive_prohibition(sentence)
        ),
        None,
    )
    if source_index is not None:
        source = sentences[source_index]
        for candidate in sentences[source_index + 1 :]:
            if (
                POSITIVE_CLAUSE.search(candidate)
                and _clauses_related(source, candidate)
            ):
                candidate_index = sentences.index(candidate, source_index + 1)
                return " ".join(sentences[candidate_index:]).strip()
    return None


def _replacement_is_concrete(text: str) -> bool:
    if VAGUE_TARGET.search(text):
        return False
    if EXPLICIT_OBSERVABLE_CHECK.search(text):
        return True
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_./:-]*", text)
    return len(words) >= 3 and bool(
        POSITIVE_CLAUSE.search(text)
        or REPLACEMENT_LABEL.search(text)
        or REPLACEMENT_TRANSITION.search(text)
    )


def evaluate_surface(surface: Surface) -> list[Finding]:
    """Apply paragraph-level policy after lexical candidates are identified."""
    if not surface.enforce or surface.kind in {"quote", "example"}:
        return []
    if surface.kind == "identifier":
        if NEGATIVE_IDENTIFIER.fullmatch(surface.text):
            return [
                _make_finding(
                    RULE_IDENTIFIER,
                    surface,
                    evidence=surface.text,
                )
            ]
        return []

    findings: list[Finding] = []
    if surface.kind == "structured_value":
        for match in NEGATIVE_IDENTIFIER_IN_VALUE.finditer(surface.text):
            findings.append(
                _make_finding(
                    RULE_IDENTIFIER,
                    surface,
                    (
                        f"identifier {match.group(0)!r} names an exclusion; "
                        "use a capability name or register an exact exemption"
                    ),
                    evidence=match.group(0),
                )
            )

    text = _normalize_text(_scrub_quoted_material(surface.text))
    prohibition = _directive_prohibition(text)
    if prohibition is None:
        return findings

    replacement = _replacement_text(text, prohibition)
    if replacement is None:
        findings.append(
            _make_finding(
                RULE_UNPAIRED,
                surface,
                evidence=text,
            )
        )
        return findings

    consequential = bool(
        BOUNDARY_LABEL.search(text) or HIGH_CONSEQUENCE.search(text)
    )
    vague = bool(VAGUE_TARGET.search(replacement))
    missing_consequential_check = bool(
        consequential and not EXPLICIT_OBSERVABLE_CHECK.search(replacement)
    )
    if vague or missing_consequential_check or not _replacement_is_concrete(
        replacement
    ):
        findings.append(
            _make_finding(
                RULE_TARGET,
                surface,
                (
                    "replacement remains vague or lacks the observable check "
                    "required for a high-consequence boundary"
                ),
                evidence=text,
            )
        )
    return findings


def _parse_failure(
    path: str,
    kind: str,
    message: str,
    *,
    reason_code: str = "",
) -> Finding:
    surface = Surface(
        path=path,
        start_line=1,
        end_line=1,
        kind=kind,
        text=(
            f"{kind}:parse-failure:{reason_code}"
            if reason_code
            else f"{kind}:parse-failure"
        ),
        location="parse",
    )
    return _make_finding(
        "LANG900_PARSE_FAILURE",
        surface,
        message,
        reason_code=reason_code,
    )


def _extract_surfaces(path: str, content: str, format_name: str) -> list[Surface]:
    normalized = format_name.lower().lstrip(".")
    if normalized in {"md", "markdown"}:
        return extract_markdown_surfaces(path, content)
    if normalized == "json":
        return extract_json_surfaces(path, content)
    if normalized in {"yaml", "yml"}:
        return extract_yaml_surfaces(path, content)
    if normalized in {"python", "py"}:
        return extract_python_surfaces(path, content)
    raise SurfaceParseError(f"unsupported authored format {format_name!r}")


def findings_for_content(
    path: str,
    content: str,
    format_name: str,
) -> list[Finding]:
    """Return findings for one in-memory artifact, including parse failures."""
    parse_kind = (
        "docstring"
        if format_name.lower().lstrip(".") in {"python", "py"}
        else "authored_prose"
        if format_name.lower().lstrip(".") in {"md", "markdown"}
        else "structured_value"
    )
    try:
        surfaces = _extract_surfaces(path, content, format_name)
    except (SurfaceParseError, UnicodeError) as exc:
        return [_parse_failure(path, parse_kind, str(exc))]
    return sorted(
        (
            finding
            for surface in surfaces
            for finding in evaluate_surface(surface)
        ),
        key=lambda item: (
            item.path,
            item.start_line,
            item.rule_id,
            item.fingerprint,
        ),
    )


def _parse_utc(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not RFC3339_UTC.fullmatch(value):
        raise ValueError(f"{field} must be an RFC 3339 UTC timestamp")
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _valid_exemption_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not any(character in value for character in "*?[]\\")
        and path.as_posix() == value
    )


def _exemption_issue(
    source_path: str,
    message: str,
    identity: str,
    line: int = 1,
    *,
    reason_code: str = "",
) -> Finding:
    surface = Surface(
        path=source_path,
        start_line=line,
        end_line=line,
        kind="structured_value",
        text=identity,
        location="exemptions",
    )
    return _make_finding(
        "LANG901_EXEMPTION_INVALID",
        surface,
        message,
        reason_code=reason_code,
    )


def load_exemptions_text(
    content: str,
    source_path: str = DEFAULT_EXEMPTIONS.as_posix(),
    as_of: dt.datetime | None = None,
) -> tuple[list[Exemption], list[Finding]]:
    """Load exact exemptions and fail closed on stale or ambiguous entries."""
    now = as_of or dt.datetime.now(dt.timezone.utc)
    try:
        document = _load_json_text(content)
    except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        return [], [
            _exemption_issue(
                source_path,
                f"Exemption configuration parsing failed: {exc}",
                str(exc),
            )
        ]
    if not isinstance(document, dict) or set(document) != {
        "policy_release",
        "exemptions",
    }:
        return [], [
            _exemption_issue(
                source_path,
                "Exemption configuration requires exactly policy_release and exemptions.",
                "configuration-shape",
            )
        ]
    if document.get("policy_release") != POLICY_RELEASE:
        return [], [
            _exemption_issue(
                source_path,
                f"Exemption policy_release must equal {POLICY_RELEASE}.",
                str(document.get("policy_release")),
            )
        ]
    entries = document.get("exemptions")
    if not isinstance(entries, list):
        return [], [
            _exemption_issue(
                source_path,
                "Exemptions must be an array.",
                "exemptions-type",
            )
        ]

    required = {
        "exemption_id",
        "rule_id",
        "path",
        "fingerprint",
        "rationale",
        "owner_role",
        "reviewed_at",
        "expires_at",
    }
    exemptions: list[Exemption] = []
    issues: list[Finding] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    for index, item in enumerate(entries):
        identity = f"exemption[{index}]"
        if not isinstance(item, dict) or set(item) != required:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{identity} requires exactly {sorted(required)}.",
                    identity,
                )
            )
            continue
        exemption_id = item["exemption_id"]
        rule_id = item["rule_id"]
        path = item["path"]
        fingerprint = item["fingerprint"]
        rationale = item["rationale"]
        owner_role = item["owner_role"]
        if (
            not isinstance(exemption_id, str)
            or not re.fullmatch(r"LANG-EX-[A-Z0-9-]{3,80}", exemption_id)
            or exemption_id in seen_ids
        ):
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{identity} has an invalid or duplicate exemption_id.",
                    str(exemption_id),
                )
            )
            continue
        if rule_id not in VALID_RULE_EXEMPTIONS:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} names a rule that accepts no exemptions.",
                    exemption_id,
                )
            )
            continue
        if not _valid_exemption_path(path):
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} path must be one exact repository-relative path.",
                    exemption_id,
                )
            )
            continue
        if not isinstance(fingerprint, str) or not FINGERPRINT.fullmatch(fingerprint):
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} fingerprint must be one SHA-256 finding fingerprint.",
                    exemption_id,
                )
            )
            continue
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} rationale must document the reviewed reason.",
                    exemption_id,
                )
            )
            continue
        if not isinstance(owner_role, str) or len(owner_role.strip()) < 3:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} owner_role must name an accountable role.",
                    exemption_id,
                )
            )
            continue
        try:
            reviewed_at = _parse_utc(item["reviewed_at"], "reviewed_at")
            expires_at = _parse_utc(item["expires_at"], "expires_at")
        except ValueError as exc:
            issues.append(
                _exemption_issue(source_path, f"{exemption_id}: {exc}", exemption_id)
            )
            continue
        if expires_at <= reviewed_at:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} expires_at must follow reviewed_at.",
                    exemption_id,
                )
            )
            continue
        if reviewed_at > now:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} reviewed_at is later than the evaluation time.",
                    exemption_id,
                )
            )
            continue
        if expires_at - reviewed_at > dt.timedelta(days=180):
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} review window exceeds 180 days.",
                    exemption_id,
                )
            )
            continue
        if expires_at <= now:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} expired at {item['expires_at']}.",
                    exemption_id,
                )
            )
            continue
        key = (rule_id, path, fingerprint)
        if key in seen_keys:
            issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption_id} duplicates an existing rule, path, and fingerprint.",
                    exemption_id,
                )
            )
            continue
        seen_ids.add(exemption_id)
        seen_keys.add(key)
        exemptions.append(
            Exemption(
                exemption_id=exemption_id,
                rule_id=rule_id,
                path=path,
                fingerprint=fingerprint,
                rationale=rationale.strip(),
                owner_role=owner_role.strip(),
                reviewed_at=reviewed_at,
                expires_at=expires_at,
            )
        )
    return exemptions, issues


def load_exemptions(
    path: Path,
    *,
    root: Path,
    as_of: dt.datetime | None = None,
) -> tuple[list[Exemption], list[Finding]]:
    """Read one bounded exemption registry and return fail-closed diagnostics."""
    content, display, reason_code = _read_repository_text(
        path,
        root,
        subject="EXEMPTION_REGISTRY",
    )
    if reason_code is not None:
        return [], [
            _exemption_issue(
                display,
                _diagnostic_message(reason_code),
                reason_code,
                reason_code=reason_code,
            )
        ]
    assert content is not None
    return load_exemptions_text(
        content,
        source_path=display,
        as_of=as_of,
    )


def apply_exemptions(
    findings: Iterable[Finding],
    exemptions: Sequence[Exemption],
    source_path: str = DEFAULT_EXEMPTIONS.as_posix(),
    report_unused: bool = True,
    as_of: dt.datetime | None = None,
) -> ScanResult:
    """Apply a registry only when every exemption matches exactly one finding."""
    now = as_of or dt.datetime.now(dt.timezone.utc)
    materialized = list(findings)
    counts = Counter(
        (item.rule_id, item.path, item.fingerprint) for item in materialized
    )
    registry_issues = [
        item for item in materialized if item.rule_id == RULE_EXEMPTION
    ]
    derived_issues: list[Finding] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    eligible: dict[tuple[str, str, str], Exemption] = {}

    for exemption in exemptions:
        identity = str(getattr(exemption, "exemption_id", "<invalid>"))
        direct_error: str | None = None
        if (
            not isinstance(exemption.exemption_id, str)
            or not re.fullmatch(
                r"LANG-EX-[A-Z0-9-]{3,80}",
                exemption.exemption_id,
            )
        ):
            direct_error = "has an invalid exemption_id"
        elif exemption.rule_id not in VALID_RULE_EXEMPTIONS:
            direct_error = "names a rule that accepts no exemptions"
        elif not _valid_exemption_path(exemption.path):
            direct_error = "path must be one exact repository-relative path"
        elif (
            not isinstance(exemption.fingerprint, str)
            or not FINGERPRINT.fullmatch(exemption.fingerprint)
        ):
            direct_error = "fingerprint must be one SHA-256 finding fingerprint"
        elif (
            not isinstance(exemption.rationale, str)
            or len(exemption.rationale.strip()) < 20
        ):
            direct_error = "rationale must document the reviewed reason"
        elif (
            not isinstance(exemption.owner_role, str)
            or len(exemption.owner_role.strip()) < 3
        ):
            direct_error = "owner_role must name an accountable role"
        elif (
            not isinstance(exemption.reviewed_at, dt.datetime)
            or exemption.reviewed_at.utcoffset() != dt.timedelta(0)
            or not isinstance(exemption.expires_at, dt.datetime)
            or exemption.expires_at.utcoffset() != dt.timedelta(0)
        ):
            direct_error = "timestamps must be timezone-aware UTC values"
        elif exemption.expires_at <= exemption.reviewed_at:
            direct_error = "expires_at must follow reviewed_at"
        elif exemption.reviewed_at > now:
            direct_error = "reviewed_at is later than the evaluation time"
        elif (
            exemption.expires_at - exemption.reviewed_at
            > dt.timedelta(days=180)
        ):
            direct_error = "review window exceeds 180 days"
        elif exemption.expires_at <= now:
            direct_error = f"expired at {exemption.expires_at.isoformat()}"
        if direct_error is not None:
            derived_issues.append(
                _exemption_issue(
                    source_path,
                    f"{identity} {direct_error}.",
                    identity,
                )
            )
            continue
        if exemption.exemption_id in seen_ids or exemption.key in seen_keys:
            derived_issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption.exemption_id} duplicates a registry identity.",
                    exemption.exemption_id,
                )
            )
            continue
        seen_ids.add(exemption.exemption_id)
        seen_keys.add(exemption.key)
        match_count = counts[exemption.key]
        if match_count == 0:
            derived_issues.append(
                _exemption_issue(
                    source_path,
                    f"{exemption.exemption_id} matched no current finding.",
                    exemption.exemption_id,
                )
            )
            continue
        if match_count > 1:
            derived_issues.append(
                _exemption_issue(
                    source_path,
                    (
                        f"{exemption.exemption_id} matched {match_count} "
                        "occurrences; each exemption must match exactly one."
                    ),
                    exemption.exemption_id,
                )
            )
            continue
        eligible[exemption.key] = exemption

    if registry_issues or derived_issues:
        return ScanResult(
            findings=tuple(
                sorted(
                    [*materialized, *derived_issues],
                    key=lambda item: (
                        item.path,
                        item.start_line,
                        item.end_line,
                        item.rule_id,
                        item.fingerprint,
                    ),
                )
            )
        )

    active: list[Finding] = []
    applied: list[AppliedExemption] = []
    for finding in materialized:
        key = (finding.rule_id, finding.path, finding.fingerprint)
        exemption = eligible.get(key)
        if exemption is None:
            active.append(finding)
            continue
        applied.append(
            AppliedExemption(
                exemption_id=exemption.exemption_id,
                rule_id=finding.rule_id,
                path=finding.path,
                fingerprint=finding.fingerprint,
                owner_role=exemption.owner_role,
                expires_at=exemption.expires_at.isoformat().replace(
                    "+00:00",
                    "Z",
                ),
            )
        )
    return ScanResult(
        findings=tuple(
            sorted(
                active,
                key=lambda item: (
                    item.path,
                    item.start_line,
                    item.end_line,
                    item.rule_id,
                    item.fingerprint,
                ),
            )
        ),
        applied_exemptions=tuple(
            sorted(applied, key=lambda item: item.exemption_id)
        ),
    )


def scan_content(
    path: str,
    content: str,
    format_name: str,
    exemptions: Sequence[Exemption] = (),
    exemption_issues: Sequence[Finding] = (),
    report_unused: bool = True,
    as_of: dt.datetime | None = None,
) -> ScanResult:
    """Evaluate an in-memory artifact for golden-corpus and editor integrations."""
    raw_findings = [
        *findings_for_content(path, content, format_name),
        *exemption_issues,
    ]
    return apply_exemptions(
        raw_findings,
        exemptions,
        report_unused=report_unused,
        as_of=as_of,
    )


def repository_files(root: Path) -> Iterable[Path]:
    """Yield authored entries without following a symbolic link target."""
    for path in sorted(root.rglob("*")):
        if not EXCLUDED_PARTS.isdisjoint(path.parts):
            continue
        if path.is_symlink():
            if path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() == ".py":
                yield path
            continue
        if not path.is_file() or not _path_resolves_within(path, root):
            continue
        relative = path.relative_to(root)
        if relative in POLICY_META_PATHS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() == ".py":
            yield path


def _read_findings(path: Path, root: Path) -> list[Finding]:
    content, relative, reason_code = _read_repository_text(
        path,
        root,
        subject="SOURCE_PATH",
    )
    if reason_code is not None:
        kind = "docstring" if path.suffix.lower() == ".py" else "structured_value"
        return [
            _parse_failure(
                relative,
                kind,
                _diagnostic_message(reason_code),
                reason_code=reason_code,
            )
        ]
    assert content is not None
    format_name = path.suffix.lower().lstrip(".")
    return findings_for_content(relative, content, format_name)


def check_text(path: Path, root: Path) -> list[Finding]:
    """Compatibility wrapper for one Markdown, JSON, or YAML artifact."""
    return _read_findings(path, root)


def check_python(path: Path, root: Path) -> list[Finding]:
    """Compatibility wrapper for one Python artifact."""
    return _read_findings(path, root)


def scan_paths(
    paths: Iterable[Path],
    root: Path,
    exemptions_path: Path | None = None,
    report_unused: bool = True,
    as_of: dt.datetime | None = None,
) -> ScanResult:
    """Scan paths and apply the repository's reviewed exemption inventory."""
    raw_findings = [
        finding for path in paths for finding in _read_findings(path, root)
    ]
    configured_path = exemptions_path or (root / DEFAULT_EXEMPTIONS)
    content, configured_display, reason_code = _read_repository_text(
        configured_path,
        root,
        subject="EXEMPTION_REGISTRY",
    )
    if reason_code is not None:
        issue = _exemption_issue(
            configured_display,
            _diagnostic_message(reason_code),
            reason_code,
            reason_code=reason_code,
        )
        return apply_exemptions(
            [*raw_findings, issue],
            (),
            source_path=configured_display,
            report_unused=False,
            as_of=as_of,
        )
    assert content is not None
    exemptions, issues = load_exemptions_text(
        content,
        configured_display,
        as_of=as_of,
    )
    result = apply_exemptions(
        [*raw_findings, *issues],
        exemptions,
        source_path=configured_display,
        report_unused=report_unused,
        as_of=as_of,
    )
    return result


def scan_repository(
    root: Path,
    exemptions_path: Path | None = None,
    as_of: dt.datetime | None = None,
) -> ScanResult:
    return scan_paths(
        repository_files(root),
        root=root,
        exemptions_path=exemptions_path,
        report_unused=True,
        as_of=as_of,
    )


def render_text(result: ScanResult) -> str:
    lines = [
        f"{POLICY_RELEASE}: status={result.as_dict()['status']} "
        f"findings={len(result.findings)} "
        f"applied_exemptions={len(result.applied_exemptions)}"
    ]
    if result.findings:
        lines.extend(f"  - {finding}" for finding in result.findings)
    if result.applied_exemptions:
        lines.append("Applied exemption receipts:")
        lines.extend(
            "  - "
            f"{item.exemption_id}: {item.rule_id} {item.path} "
            f"[{item.fingerprint}] owner={item.owner_role} "
            f"expires={item.expires_at}"
            for item in result.applied_exemptions
        )
    return "\n".join(lines)


def render_json(result: ScanResult) -> str:
    return json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"


def _sarif_artifact_uri(path: str) -> str:
    """Encode one repository-relative path as an RFC 3986 URI-reference."""
    return quote(path, safe="/-._~")


def render_sarif(result: ScanResult) -> str:
    levels = {"error": "error", "warning": "warning", "note": "note"}
    document = {
        "$schema": (
            "https://json.schemastore.org/sarif-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "site-reading-language-policy",
                        "semanticVersion": POLICY_RELEASE.removeprefix(
                            "language-policy-v"
                        ),
                        "rules": [
                            {
                                "id": rule_id,
                                "shortDescription": {
                                    "text": rule["message"],
                                },
                                "help": {"text": rule["help"]},
                                "defaultConfiguration": {
                                    "level": levels[rule["severity"]],
                                },
                            }
                            for rule_id, rule in RULES.items()
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": finding.rule_id,
                        "level": levels[finding.severity],
                        "message": {"text": finding.message},
                        "partialFingerprints": {
                            "languagePolicyFingerprint/v1": finding.fingerprint,
                        },
                        **(
                            {
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {
                                                "uri": _sarif_artifact_uri(
                                                    finding.path
                                                )
                                            },
                                            "region": {
                                                "startLine": finding.start_line,
                                                "endLine": finding.end_line,
                                            },
                                        },
                                        "logicalLocations": [
                                            {
                                                "name": finding.location
                                                or finding.surface_kind,
                                                "kind": finding.surface_kind,
                                            }
                                        ],
                                    },
                                ]
                            }
                            if finding.path != "<outside-root>"
                            else {}
                        ),
                        "properties": {
                            "surfaceKind": finding.surface_kind,
                            "policyRelease": POLICY_RELEASE,
                            **(
                                {"reasonCode": finding.reason_code}
                                if finding.reason_code
                                else {}
                            ),
                        },
                    }
                    for finding in result.findings
                ],
                "invocations": [
                    {
                        "executionSuccessful": result.exit_code != 2,
                        "exitCode": result.exit_code,
                    }
                ],
                "properties": {
                    "schemaVersion": OUTPUT_SCHEMA_VERSION,
                    "policyRelease": POLICY_RELEASE,
                    "status": result.as_dict()["status"],
                    "appliedExemptions": [
                        item.as_dict() for item in result.applied_exemptions
                    ],
                },
            }
        ],
    }
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def report(findings: Iterable[Finding]) -> int:
    """Retain the former report API for downstream callers."""
    result = ScanResult(tuple(findings))
    print(render_text(result))
    return result.exit_code


def check_content(
    path: str,
    content: str,
    *,
    format_hint: str | None = None,
) -> list[Finding]:
    """Compatibility API for in-memory qualification runners."""
    selected = format_hint or Path(path).suffix.lstrip(".")
    return findings_for_content(path, content, selected)


def _coerce_result(
    value: ScanResult | Sequence[Finding],
) -> ScanResult:
    return value if isinstance(value, ScanResult) else ScanResult(tuple(value))


def text_report(value: ScanResult | Sequence[Finding]) -> str:
    return render_text(_coerce_result(value))


def json_report(value: ScanResult | Sequence[Finding]) -> str:
    return render_json(_coerce_result(value))


def sarif_report(value: ScanResult | Sequence[Finding]) -> str:
    return render_sarif(_coerce_result(value))


def exit_code(value: ScanResult | Sequence[Finding]) -> int:
    return _coerce_result(value).exit_code


SourceUnit = Surface


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate structure-aware, negation-aware authored language."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Repository-relative files or directories; defaults to the repository.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        default="text",
        dest="output_format",
    )
    parser.add_argument(
        "--exemptions",
        type=Path,
        default=None,
        help="Reviewed exemption registry; defaults to language-policy/exemptions.json.",
    )
    return parser


def _resolve_requested_paths(
    root: Path,
    arguments: Sequence[Path],
) -> list[Path]:
    if not arguments:
        return list(repository_files(root))
    resolved: list[Path] = []
    for argument in arguments:
        candidate = argument if argument.is_absolute() else root / argument
        if candidate.is_symlink() or not _path_resolves_within(candidate, root):
            resolved.append(candidate)
            continue
        if candidate.is_dir():
            resolved.extend(
                path
                for path in repository_files(root)
                if _path_resolves_within(path, candidate)
            )
        else:
            resolved.append(candidate)
    return sorted(set(resolved))


def check_repository(
    root: Path,
    selected_paths: Sequence[Path] | None = None,
    *,
    exemptions_path: Path | None = None,
    as_of: dt.datetime | None = None,
) -> ScanResult:
    """Canonical repository API with bounded optional path selection."""
    paths = _resolve_requested_paths(root, selected_paths or ())
    return scan_paths(
        paths,
        root=root,
        exemptions_path=exemptions_path,
        report_unused=selected_paths is None,
        as_of=as_of,
    )


def main(root: Path, argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = _resolve_requested_paths(root, args.paths)
    exemptions_path = args.exemptions
    if exemptions_path is not None and not exemptions_path.is_absolute():
        exemptions_path = root / exemptions_path
    result = scan_paths(
        paths,
        root=root,
        exemptions_path=exemptions_path,
        report_unused=not bool(args.paths),
    )
    renderer = {
        "text": render_text,
        "json": render_json,
        "sarif": render_sarif,
    }[args.output_format]
    print(renderer(result), end="")
    return result.exit_code
