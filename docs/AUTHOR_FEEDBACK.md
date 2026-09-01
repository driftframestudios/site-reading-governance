# Vale Author Feedback

## Purpose and authority

Vale supplies structure-aware feedback while collaborators write and review
governance material. It examines authored Markdown prose and Python comments.
The deterministic language check in `tools/check_language.py` remains part of
the standing local candidate proof. The manual `governance-validation` job
exercises the same check after a separately reviewed activation.

The separate `author-feedback` job is advisory. Its result stays outside the
stable aggregate gate and outside repository promotion evidence.

## Scope

The repository-owned configuration examines:

- Markdown headings, paragraphs, lists, and table prose;
- Python line comments and block comments; and
- observable target-state, evidence-grounding, referent, and sentence-shape
  opportunities.

Vale's markup parser excludes fenced code, indented code, inline code, scripts,
styles, preformatted blocks, and quoted diagnostic examples. Python processing
selects comments while preserving executable source as code.

| Rule | Severity | Review outcome |
| --- | --- | --- |
| `SiteReading.TargetState` | warning | Lead with an observable state and pair a hard boundary with safe replacement behavior. |
| `SiteReading.EvidenceGrounding` | suggestion | Replace emphasis with an observation, source, or explicit condition. |
| `SiteReading.AmbiguousReferent` | suggestion | Name a subject when several referents remain plausible. |
| `SiteReading.SentenceComplexity` | suggestion | Split a comma-dense sentence when its decision path becomes difficult to follow. |

Warnings merit author review. Suggestions invite judgment and can remain when
the surrounding context already supplies clarity.

## Reproducible operation

CI downloads the immutable
[`vale_3.15.2_Linux_64-bit.tar.gz`](https://github.com/vale-cli/vale/releases/download/v3.15.2/vale_3.15.2_Linux_64-bit.tar.gz)
release asset and requires SHA-256
`fc72e64454d6bd7af91905d4faebbf411bae3eec17bb572f4101311212bc0d9e`
before extraction. The workflow invokes the verified binary directly; it
introduces zero reviewdog or language-action runtime. The repository carries
every active style under `.vale/styles` and declares zero remote packages in
`.vale.ini`.

The advisory job runs on pull requests with read-only repository contents and
writes findings to its workflow log. Push validation continues through the
deterministic aggregate without invoking Vale.

For local feedback, install Vale `3.15.2` and run:

```sh
vale --config=.vale.ini --no-global .
```

The repository default includes both warnings and suggestions for local
authors. CI requests `--minAlertLevel=warning`, which keeps the pull-request
log focused on the higher-signal warning tier while suggestions remain
available during local composition.

`tools/check_language.py` and the other blocking validation commands continue
to determine candidate eligibility.

## Change stewardship

Changes to `.vale.ini`, `.vale/styles`, or the advisory workflow receive
repository-owner review. A Vale version advance updates the release URL,
expected digest, local qualification evidence, and this document in one
ordinary branch, review, and validation path.
