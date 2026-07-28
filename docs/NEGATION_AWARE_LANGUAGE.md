# Negation-aware Language

## Source and application

This repository applies the collaboration pattern documented in
[Semantic Attractor Design — Negation-Aware Instructions](https://app.notion.com/p/abcb29b960a842ce8f1a409408a29257),
retrieved July 28, 2026.

The governing question is:

> What is the desired end state, and how can a collaborator verify it?

Instructions lead with the state the system should create, preserve, and
optimize. This gives people and automated collaborators a stable target.

## Strength ladder

| Rung | Form | Example |
| --- | --- | --- |
| 1 | Free-standing negation | “The response is not unstable.” |
| 2 | Established lexicalized antonym | “The response is stable.” |
| 3 | Positive constitutive predicate | “Every replay returns the same result.” |

Rung three is the default for authored guidance. Rung two is useful when a
familiar, compositionally clear word expresses the target precisely.

## Repository rules

- Comments state the invariant: `# Context stays intact across retries.`
- Identifiers state capability: `preserve_context` and `stable_response`.
- Acceptance criteria name observable success.
- Failure descriptions travel with recovery behavior.
- Paired catalogs place each risk beside the desired replacement.
- Quoted source material remains verbatim and is marked as quoted or diagnostic.

## Safety and privacy

Explicit negation carries materially meaningful hard boundaries. The positive
anchor leads where practical, and the boundary names its replacement:

```text
Credentials stay in the approved secret manager. They must not enter logs;
redacted credential references provide the operational replacement.
```

This pairing preserves the exact prohibition and supplies the next safe action.

## Code example

```python
def preserve_context(session: Session) -> VerifiedContext:
    """Return context whose integrity has been verified for this turn."""
    context = session.load_context()
    context.verify_integrity()
    return context
```

The comment, identifier, and verification step all point toward the desired
state.

## Review prompts

1. What target state does this instruction create?
2. Which observation verifies that state?
3. Does each hard boundary provide a safe replacement behavior?
4. Do comments and identifiers reinforce the same invariant?
5. Does failure language lead into an owned recovery path?

## Authoritative language assurance

`tools/language_policy_core.py` implements policy release
`language-policy-v1.0.0`; `tools/check_language.py` supplies this repository's
bounded-root wrapper. The standard-library-only reader separates:

- authored Markdown paragraphs from quotations, diagnostic sections, and
  fenced examples;
- JSON string values from structural keys;
- conservative YAML scalar values from keys and comments; and
- Python comments, docstrings, and identifiers from executable operators.

Lexical signals nominate a paragraph for review. The policy decision then
examines the complete logical paragraph for an affirmative target, a usable
replacement route, and—at high-consequence boundaries—observable
verification. This preserves literal quoted material while keeping authored
instructions actionable.

Stable rule identifiers support editor, CI, and evidence integrations:

| Rule | Policy meaning |
| --- | --- |
| `LANG001_UNPAIRED_PROHIBITION` | A prohibition needs an affirmative target and replacement in the same logical paragraph. |
| `LANG002_NEGATIVE_IDENTIFIER` | An identifier names the desired capability. |
| `LANG003_UNVERIFIABLE_TARGET` | A consequential target names its observable verification. |
| `LANG900_PARSE_FAILURE` | The bounded reader requires fully parseable source. |
| `LANG901_EXEMPTION_INVALID` | Exemption inventory remains exact, current, and exercised. |

Each finding carries severity, surface kind, source span, and a normalized
SHA-256 fingerprint. The fingerprint remains stable across line movement and
canonically equivalent Unicode while changing when the rule, path, surface, or
material text—including letter case—changes. Fingerprint material uses NFC,
collapsed whitespace, and preserved case; the policy release stays outside the
material so a release label alone cannot invalidate an exact finding identity.

## Output and exit contract

```bash
python3 tools/check_language.py
python3 tools/check_language.py --format json
python3 tools/check_language.py --format sarif
python3 tools/check_language.py docs/SECURITY-OPERATIONS.md
```

Text serves local review. JSON supplies the versioned status, findings,
summary, exit result, and applied-exemption receipts. SARIF 2.1.0 supplies rule
metadata, physical and logical locations, partial fingerprints, invocation
status, and the same applied receipts for code-scanning integrations.

Exit `0` means the selected surface satisfies policy. Exit `1` means actionable
language findings remain. Exit `2` means parsing or exemption configuration
requires repair, so candidate eligibility stays closed.

Repository traversal resolves each candidate beneath the selected root before
reading it. Every symbolic-link selection produces a typed integrity finding,
including links whose targets remain inside the root; repository-owned regular
files provide the scan surface. Missing, unreadable,
non-regular, invalid-encoding, and out-of-root selections use stable reason
codes and repository-relative paths or the `<outside-root>` placeholder.
Text, JSON, and SARIF output therefore remains portable across checkout
locations and excludes host exception text.

## Reviewed exemptions

The registry at `language-policy/exemptions.json` supports exact, temporary
exceptions. Each entry binds one rule, one repository-relative path, and one
finding fingerprint. It also records:

- an accountable `owner_role`;
- a substantive `rationale`;
- `reviewed_at` and `expires_at` UTC timestamps; and
- an exemption identity suitable for review evidence.

Review windows extend at most 180 days and begin no later than evaluation.
Each exemption matches exactly one occurrence. Expired, future-reviewed,
overbroad, duplicate, multiply matched, and unused entries produce
`LANG901_EXEMPTION_INVALID`. One invalid entry keeps the entire registry from
suppressing findings; valid runs retain an applied receipt containing the
owner, expiry, path, rule, and fingerprint. The empty default registry
demonstrates that candidate source currently requires zero exceptions.

## Executable policy corpus

`language-policy/corpus-v1.json` is the versioned behavioral contract. It
contains 89 `should_flag`, `should_pass`, `exempt`, and
`exemption_invalid` cases across Markdown, JSON, YAML, and Python. Exact
expected rule, severity, surface, line, fingerprint, and applied-receipt
results provide regression evidence for detection, precision, and fail-closed
exception handling.

`language-policy/manifest.json` is the byte-stable projection contract. It pins
the canonical core and union corpus, records their governance and downstream
paths, and carries the rules and severities, formats and surface kinds, exit
meanings, fingerprint and output-schema contracts, exact exemption
multiplicity, all-or-nothing registry behavior, and typed repository I/O reason
codes used for cross-repository conformance.

The typed `language-control.schema.json` contract carries consequential
instructions as explicit target, boundary, replacement, verification,
ownership, and evidence fields. Narrative prose remains readable; material
controls gain a machine-verifiable operational form.

## Semantic expansion boundary

[`SEMANTIC_SHADOW_REVIEW.md`](SEMANTIC_SHADOW_REVIEW.md) defines an inactive,
documentation-only contract for future statistical or model-assisted review.
It bounds authority, input, privacy, reproducibility, evaluation, promotion,
and recovery before such a reviewer can enter offline qualification.

The deterministic checker remains the machine candidate-eligibility control.
Vale and any future semantic reviewer supply advisory candidates, while
accountable people retain authorship, repository promotion, and domain
acceptance.
