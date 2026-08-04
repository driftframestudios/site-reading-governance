# Negation-aware Language

The governing question is: **What desired state should the collaborator create,
and what observation verifies it?**

## Writing pattern

- Lead with the target state.
- Name invariants in comments and identifiers.
- Pair a materially meaningful boundary with a safe replacement behavior.
- Connect a failure description to recovery or the next useful action.
- Preserve quoted source material verbatim and identify it as quotation.

Example:

```text
Credentials stay in the approved secret manager. They must not enter logs;
redacted secret references provide the operational replacement.
```

The explicit boundary preserves safety while the first and final clauses give a
collaborator a usable semantic target.

## Active implementation

Vale applies the repository-owned `SiteReading.TargetState` rule to authored
paragraphs and comments. The rule flags prohibition-shaped language when the
same paragraph lacks replacement or recovery language. Additional Vale rules
surface unsupported emphasis, ambiguous referents, and high sentence density.

```sh
vale --config=.vale.ini --no-global .
```

The prior custom language analyzer, corpus, exemption registry, fingerprints,
and SARIF projection remain historical design material. Vale now supplies the
active implementation through a maintained framework and a small configuration.
