---
title: Population claim review
version: 0.1.0
status: working
audience: Population reviewers and comparison maintainers
source_band: public_possible
task_type: population_claim_review
---
# Population claim review 0.1

Return a statement whose construction, denominator, omissions, and review
standing are visible together. Completion gives the next reviewer an allowed
interpretation and the exact evidence needed to broaden it.

## Entry and authority

Receive the exact proposed statement, intended use, admitted pack/study/report,
represented and omitted dimensions, population purpose, and modeled reviewer.
Program owns population construction and observations; Comparative owns scoring;
Governance carries the allowed interpretation and review record.

Simulation owns this authored population; Program owns its admitted study
representation. Enter with the [optional owner profile](../../docs/ADMINISTRATIVE_ASSURANCE.md#receive-a-complete-study)
and a local synthetic-validation grant. Unavailable inputs return to their
source owner while the proposed population statement stays held.

## Checks and exercise

1. Receive the three artifacts together through the companion receiver.
2. Read planned, attempted, completed, usable, scored, pending, failed,
   cancelled, abstained, and excluded counts with their owner-defined meanings.
3. Inspect the report's group denominators, independent subjects, repeated
   observations, small-cell standing, and empty cohort. Repeats retain their
   within-subject relation. Calibration and representative-population claims
   require separate evidence.
4. Exercise the 144-run authored pack. Expect 128 scored runs and four designed
   scientific-output disagreements. Inspect the unchanged-input control and
   designed administrative difference in the received report.
5. Carry a descriptive output-comparison statement into modeled review. Keep a
   population-effect statement held for its population-use evidence.

### Executable control, small-cell, and omission exercises

Run `test_assurance_exercises.py` through the [index command](index.md#run-the-bounded-exercises).
`test_population_controls_omissions_and_held_scientific_interpretation` checks
literal populations: 144 planned, 136 attempted, 128 completed/usable/scored,
four each pending/abstained/failed/excluded, and zero cancelled. The unchanged
`REPEAT` control retains identical administrative and scientific outputs.
`REPORTABILITY` changes review/10 minutes to submit/5 minutes while preserving
scientific output. Those authored differences support harness interpretation.

The request records population prevalence, real payer outcomes, service
effectiveness, and independent calibration as omissions. An empty omission
list receives `record_shape`. The population-effect statement remains held;
the service interpretation uses the existing claim-veracity schema with
`local_measurement_needed` and candidate settlement. A valid schema establishes
the recorded posture; the named reviewer owns its material suitability.

`test_small_cells_withhold_estimates_while_full_population_remains_visible`
raises the admitted pack's display threshold to 32 independent subjects. The
ADULT-EN cohort still has 72 planned runs, 64 scored runs, 28 complete pairs,
and 14 subjects, but its estimate is withheld as `small_cell`. The authored
empty cohort remains `empty`, and total planned/scored counts stay 144/128.
Represented factor names come from the admitted specification; omitted
dimensions remain an explicit review input, rather than inferred population
coverage.

## Recovery and stopping event

A missing or inconsistent artifact returns to its named producer. A proposed
population claim can narrow to the authored workflow or harness question while
representativeness remains open. Stop when the reviewer can locate construction,
omissions, denominator, small-cell posture, allowed statement, and review state.

## Handback and acceptance event

Return one companion and its exact source references. The focused upstream
exercise establishes fixture admission and receiving consistency. The modeled
review acknowledges that bounded result; an accountable population-use decision
receives its own evidence and authority.
