# Vale author feedback

Use Vale while editing a passage or reviewing a change. Its rules locate wording
that deserves a second reading. Authors and reviewers decide whether a change
would help the reader. The deterministic [language policy](../language-policy/README.md)
separately governs candidate eligibility.

## Read a finding in context

The shared `SiteReading` style reads Markdown prose and Python comments,
including docstrings. Markdown block quotations, inline and fenced code, and
ordinary Python string values preserve their source wording. Read an alert with
the surrounding paragraph, heading or example before deciding what to retain.

| Rule | Severity | What to inspect |
| --- | --- | --- |
| `SiteReading.TargetState` | warning | A paragraph or list item contains a short directive such as “Never …” on its own, or ends with a vague pointer such as “the recovery path is documented somewhere.” Can the reader identify the available action? |
| `SiteReading.EvidenceGrounding` | suggestion | Does the passage give the reader grounds for a claim introduced by emphasis? |
| `SiteReading.AmbiguousReferent` | suggestion | Can the reader identify which subject a phrase such as “This is” refers to? |
| `SiteReading.SentenceComplexity` | suggestion | Can the reader follow the decision through a sentence with several commas? |

Keep the precise wording of a safety instruction. When a reviewer cannot tell
what to do next, name the action, its object and the person or procedure that
receives it. A concrete instruction like “Send it to the designated reviewer”
can supply that direction in the same paragraph or list item, including across
wrapped lines.

Read modal wording in its domain context. “The instrument must not drift” may
state an acceptance condition. An “unless” clause can identify an exception
that an author needs to preserve. The rule can flag either one. A comma, an
internal period or a second sentence can also take a directive outside the
standalone pattern. A quiet result means the selected patterns did not match.
Review the actual action and condition when either matters to the reader.

## Run the pinned tool

Use Vale `3.15.2`. The default includes both warnings and suggestions. Pick a
changed file for a local review, or supply the repository directory for a
broader pass.

```sh
vale --config=.vale.ini --no-global docs/NEGATION_AWARE_LANGUAGE.md
vale --config=.vale.ini --no-global .
```

To qualify the rules themselves, run the following command with the pinned
binary on `PATH`.

```sh
python3 .vale/qualify.py
```

The qualifier writes synthetic `.md` and `.py` files into a temporary directory,
checks the running Vale version, then runs the fixtures together in one engine
process. Each file exercises a known match alongside examples whose wording
should stay quiet. The comparison matches the exact fixture paths and counts
each occurrence of a rule, severity and positive integer line. The order of
rows and their explanatory text can vary. A successful run establishes that
these fixtures received the expected findings.

The version check and fixture run each have a ten-second timeout. A process
that cannot run, a malformed report, or a difference from the authored
expectations stops qualification. Restore the pinned executable for a process
failure. For a fixture difference, inspect the named file and the rule before
using that rule to review a passage.

## Test the qualifier

A rule author can exercise the report comparison directly with Python's
standard library. From the repository root, run:

```sh
python3 -m doctest .vale/qualify.py
```

To reproduce the optional parameterized tests on macOS or Linux, use `uv` and
an isolated CPython 3.12 environment. The following commands create a temporary
environment, install its hash-pinned test dependencies and run the tests.

```sh
vale_test_env="$(mktemp -d)"
uv venv --python 3.12 --managed-python "$vale_test_env"
uv pip install --python "$vale_test_env/bin/python" --require-hashes -r .vale/requirements-pytest.txt
"$vale_test_env/bin/python" -m pytest -q -p no:cacheprovider --doctest-modules .vale/qualify.py .vale/test_qualify.py
```

These tests exercise duplicate findings, malformed JSON, type and file
mismatches, and the recovery from a missing or stalled process using synthetic
inputs. The separate pinned-engine qualification exercises Vale's own markup
handling and rule execution.

## Manual workflow and downstream use

The manual Governance workflow runs the qualifier and a separate author review
when a maintainer enables `ENABLE_GITHUB_ACTIONS` and confirms the dispatch.
It checks the [Linux release archive](https://github.com/vale-cli/vale/releases/download/v3.15.2/vale_3.15.2_Linux_64-bit.tar.gz)
against SHA-256 `fc72e64454d6bd7af91905d4faebbf411bae3eec17bb572f4101311212bc0d9e`.
Its advisory prose pass uses `--minAlertLevel=warning`. The automatic
pull-request workflow runs the deterministic checker. Reviewers can run the
local suggestion tier on the files they are changing.

Governance owns `.vale.ini`, `.vale/styles/SiteReading/`, and the qualifier and
test files in `.vale/`. A receiving repository can copy those files from one
reviewed revision, compare the bytes, and run the same qualification. The
receiving owner reviews local terminology and retains its own configuration for additional styles. When a
rule or the Vale version changes, review the fixtures, release coordinate,
checksum and rule behavior together. A receiver can restore its preceding
reviewed files and rerun the same examples.
