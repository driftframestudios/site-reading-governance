# Source and claim invalidation 0.1

## Entry and authority

Receive a material change to source, oracle, specification, execution, catalog,
policy, scoring, capability, or intended use. Record its owner and reason. The
prior companion and source artifacts remain immutable comparison inputs.

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

## Recovery and stopping event

Unknown change keys return `change_binding` to the reviewer. A corrected source
receives new admission, evaluation, and a fresh companion. Stop when affected
claims, unaffected claims, source owner, safe current behavior, and next review
are explicit.

## Handback and acceptance event

Return the successor, reason, and named source owner. The focused exercises cover
policy and intended-use changes, selective invalidation, and prior preservation.
Production invalidation and organizational acceptance retain their own receivers.
