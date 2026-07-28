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

The repository check in `tools/check_language.py` detects common prohibition
phrases and accepts an explicit safety/privacy boundary when its replacement
behavior appears on the same logical line.

