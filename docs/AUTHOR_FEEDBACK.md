# Vale Editorial Validation

Vale is the repository's active prose framework. It reviews Markdown and Python
comments through repository-owned styles in `.vale/styles/SiteReading`.

| Rule | Level | Target |
| --- | --- | --- |
| `TargetState` | warning | Pair hard boundaries with observable replacement behavior |
| `EvidenceGrounding` | suggestion | Support emphasis with an observation, source, or condition |
| `AmbiguousReferent` | suggestion | Name the subject when several referents are plausible |
| `SentenceComplexity` | suggestion | Split comma-dense decision paths |

CI downloads Vale 3.15.2 from its published release, verifies the pinned SHA-256
digest, and runs the warning tier as a required job. Local authors can include
the suggestion tier:

```sh
vale --config=.vale.ini --no-global .
```

Changes to the Vale version, checksum, configuration, or styles travel together
through ordinary repository review.
