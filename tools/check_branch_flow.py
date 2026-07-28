#!/usr/bin/env python3
"""Check pull-request branch coordinates against the GitFlow-like contract."""

from __future__ import annotations

import argparse
import re
import sys


BRANCH_PATTERN = re.compile(
    r"^(?:main|develop|"
    r"(?:feature|fix|chore|hotfix)/[a-z0-9]+(?:-[a-z0-9]+)*|"
    r"forecast/(?:20[0-9]{2})-q[1-4]-r[1-9][0-9]*|"
    r"evidence/[a-z0-9]+(?:-[a-z0-9]+)*|"
    r"release/(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)|"
    r"support/(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))$"
)


def allowed_sources(base: str) -> tuple[str, ...]:
    """Return the source families that advance the selected target."""
    if base == "main":
        return ("release/", "hotfix/")
    if base == "develop":
        return (
            "feature/",
            "fix/",
            "chore/",
            "forecast/",
            "evidence/",
            "release/",
            "hotfix/",
            "support/",
        )
    if base.startswith("release/"):
        return ("fix/", "chore/")
    if base.startswith("support/"):
        return ("fix/", "hotfix/")
    return ()


def check_flow(base: str, head: str) -> list[str]:
    """Return actionable differences for one proposed merge coordinate."""
    findings: list[str] = []
    if BRANCH_PATTERN.fullmatch(base) is None:
        findings.append(f"target branch {base!r} is outside the branch naming contract")
    if BRANCH_PATTERN.fullmatch(head) is None:
        findings.append(f"source branch {head!r} is outside the branch naming contract")
    families = allowed_sources(base)
    if families and not head.startswith(families):
        findings.append(
            f"source branch {head!r} should use one of {', '.join(families)} "
            f"for target {base!r}"
        )
    if not families and BRANCH_PATTERN.fullmatch(base):
        findings.append(f"target branch {base!r} is a source branch rather than a merge target")
    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.base and not args.head:
        print("Branch-flow check skipped for a non-pull-request event.")
        return 0
    if bool(args.base) != bool(args.head):
        print("Branch-flow check requires both base and head coordinates.")
        return 2
    findings = check_flow(args.base, args.head)
    if findings:
        print("Branch-flow check found coordinate differences:")
        for finding in findings:
            print(f"  - {finding}")
        return 1
    print(f"Branch-flow check passed: {args.head} -> {args.base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
