# Administrative assurance runbooks

Choose the route by the decision that needs evidence. Each route uses the
[assurance companion guide](../../docs/ADMINISTRATIVE_ASSURANCE.md) and preserves
Program's domain meanings and Governance's assurance authority.

| Trigger | Route | Contract and receiving result |
| --- | --- | --- |
| A statement concerns a population or subgroup | [Population claim review](population-claim-review.v0.1.md) | Administrative assurance and claim-veracity: scoped statement, denominator, omissions, review standing |
| A proposed administrative action needs review or correction | [Decision assurance and recourse](administrative-decision-assurance-and-recourse.v0.1.md) | Program AdministrativeDecision and Governance companion: preserved proposal, owned review, reversible next move |
| Policy, source, purpose, or implementation changes | [Source and claim invalidation](source-and-claim-invalidation.v0.1.md) | Companion dependency bindings: affected claims held in an immutable successor |
| Another repository receives the contract | [Governance contract handoff](governance-contract-handoff.v0.1.md) | Source schemas, mapped examples, pinned owner profile, and one next receiver |

The named exercises use wholly synthetic inputs and modeled roles. Optional
external-source review starts through its own source and execution approval.

## Run the bounded exercises

From the repository root, use the isolated profile in
[`requirements-assurance.txt`](../../requirements-assurance.txt):

```sh
python -m unittest discover -s tests -p 'test_assurance_exercises.py' -v
```

The dependency-free route checks links and runbook metadata. The optional
profile additionally exercises actual Program admission, Simulation source
binding, Comparative scoring, and Governance review. An optional-profile skip
establishes the route's availability boundary; complete exercise evidence comes
from a profile-enabled run. These working procedures await independent review
and accepted integration under Governance #39. Their source-workbench standing
is separate from a tagged public package.
