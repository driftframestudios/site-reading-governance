---
title: Source and claim invalidation
version: 0.1.0
status: working
audience: Evidence owners and assurance reviewers
source_band: public_possible
task_type: claim_invalidation
---
# Source and claim invalidation 0.1

Return a successor that holds affected claims while preserving independent
claims and earlier bytes. Completion names the safe current behavior and the
source admission or review that can reopen the held statement.

## Entry and authority

Receive a material change to source, oracle, specification, execution, catalog,
policy, scoring, capability, or intended use. Record its owner and reason. The
prior companion and source artifacts remain immutable comparison inputs.

Enter through the [companion contract](../../docs/ADMINISTRATIVE_ASSURANCE.md#review-correction-and-recovery)
with a local invalidation grant. If the changed owner or binding is unresolved,
retain the prior record and return that missing fact before a transition.

## Checks and exercise

1. Select the changed profile bindings. Each claim type has an explicit complete
   dependency set; the receiver requires that set during admission.
2. Call `invalidate` with those bindings, a distinct successor ID, and the reason.
3. For a policy-effective-date correction, hold study-dependent claims while a
   separate composition-only claim retains its standing.
4. For an intended-use change, hold each claim that depends on that use. A changed
   contract routes through the affected artifact binding and its typed owner.
5. Confirm the earlier record's bytes are preserved, the successor records its
   identity and digest, and affected claims point to fresh admission and review.

Run `test_assurance_exercises.py` through the [index command](index.md#run-the-bounded-exercises).
`test_policy_date_and_intended_use_changes_hold_their_own_dependents` first
observes the admitted `DATE` fixture: service day `2027-01-01` yields `expired`.
It then models a policy-owner effective-window correction, holds the reviewed
output claim, and preserves reviewed capability composition. The existing
pack remains source-owned; a changed policy awaits its owner's successor pack
and evaluation. Recording an invalidation establishes the hold, rather than
the validity of that prospective source change.

Changing intended use from fixture review to service-use assessment
holds every dependent claim. Both successors bind the original identity and
digest, preserve its bytes, and retain pending configured-execution standing.
Correction resumes through fresh admission; review alone leaves invalidated
evidence held. Jurisdiction, vocabulary, and population-purpose changes route
through the policy, catalog, specification, or intended-use owner that contains
their meaning; the current profile keeps its existing finite binding vocabulary.

## Recovery and stopping event

Unknown change keys return `change_binding` to the reviewer. A corrected source
receives new admission, evaluation, and a fresh companion. Stop when affected
claims, unaffected claims, source owner, safe current behavior, and next review
are explicit.

## Handback and acceptance event

Return the successor, reason, and named source owner. The focused exercises cover
policy and intended-use changes, selective invalidation, and prior preservation.
Production invalidation and organizational acceptance retain their own receivers.
