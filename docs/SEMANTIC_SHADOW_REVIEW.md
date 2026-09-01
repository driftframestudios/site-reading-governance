# Semantic Shadow Review Contract

## Status

| Coordinate | Value |
| --- | --- |
| Language policy | `language-policy-v1.0.0` |
| Contract state | `inactive_design_contract` |
| Operational surface | Zero semantic models, prompts, endpoints, dependencies, workflow jobs, or API calls |
| Permitted future effect | Structured advisory review candidate |

This contract defines the evidence required before a statistical or
model-assisted language reviewer enters offline evaluation. The current
assurance stack remains deterministic parsing, typed high-consequence controls,
advisory Vale feedback, and accountable human review.

## Purpose and authority

A future semantic reviewer may identify paraphrased boundaries, vague
replacement behavior, ambiguous consequential language, and other candidates
that lexical rules may leave for human interpretation.

The deterministic checker remains the machine candidate-eligibility control.
Typed controls remain the machine-verifiable form for consequential
instructions. Accountable people retain author, repository, Scientific,
Quality, Regulatory, Security, Privacy, Operations, and production decisions.

The semantic reviewer has one effect: append a structured advisory candidate to
a governed evaluation record. Finding suppression, exemption creation, source
edits, pull-request approval, release promotion, receipt closure, evidence-mode
changes, and domain acceptance remain outside its effect ceiling. A reviewer
disposition and the ordinary repository controls provide the replacement path,
and the evaluation receipt verifies the resulting state.

## Bounded input

The deterministic structure parser supplies one logical authored unit together
with its repository-relative path, source span, surface kind, and nearest
heading. Each request carries at most 8 KiB of UTF-8 input. Qualification
sampling includes both candidate units and stratified clean units so that
precision and recall remain measurable.

Eligible inputs are repository-authored prose, comments, and docstrings whose
data classification permits the selected processor. Quotations, fenced code,
generated output, vendor material, regulated records, secret-shaped content,
and material above the approved classification remain outside hosted review.
An approved local reviewer or accountable human review provides the route for
material whose processor approval is absent.

Candidate text enters a delimited data field under a fixed reviewer
instruction. The reviewer receives an empty tool allowlist, zero repository
write capability, zero delegation depth, and egress limited to its approved
inference endpoint. Repository text and embedded instructions therefore remain
input data. A versioned response schema admits only the declared advisory
fields.

## Privacy and information handling

Every run records input classification, processor, processing region,
retention posture, and encryption posture. Hosted processing uses an approved
processor agreement with provider training disabled and the approved retention
window. A secret-shape scan and classification check complete before
transmission.

Outputs inherit at least the input classification because a rationale can
reconstruct source meaning. Repository receipts retain digests and structured
dispositions by default. Raw prompts and responses requiring retention travel
to the approved governed evidence store with its access and deletion policy.

## Reproducible coordinates

An evaluation manifest binds:

- repository commit, language-policy release, parser version, and corpus digest;
- immutable model snapshot or local artifact digest;
- provider and API version for a hosted model;
- exact prompt bytes and SHA-256 digest;
- response-schema version and digest;
- decoding parameters, seed where supported, and retry budget;
- runner commit and container or environment digest;
- qualification split seed and adjudication version; and
- processing region, retention class, and accountable owner roles.

A hosted coordinate whose provider can change behavior in place remains in
offline exploration. A successor model, prompt, runner, parser, response
schema, or input policy begins a fresh qualification record.

## Qualification and promotion

The qualification corpus is locked before evaluation. Two reviewers label the
holdout independently, and a named adjudicator resolves differences. The
holdout covers every eligible surface, released rule family, consequence class,
paraphrase family, clean counterexample, and instruction-injection case.

Promotion from offline evaluation to hidden shadow collection requires all of
the following:

| Measure | Minimum evidence |
| --- | --- |
| Input-boundary and structured-output conformance | 100% |
| High-consequence recall | Point estimate at least 95%; lower 95% Wilson bound at least 90% |
| Actionable precision | Point estimate at least 80%; lower 95% Wilson bound at least 70% |
| Repeated normalized-label agreement | At least 98% across three runs at the same coordinates |
| Privacy, egress, tool, write, delegation, and authority boundary | Zero violations |
| Slice reporting | Every eligible surface and consequence class reported beside the aggregate |

These measures assess reviewer usefulness rather than domain sufficiency.
Scientific, Quality, and Regulatory interpretation continues through
accountable human review.

Visible author annotations require a second accountable decision after a
predeclared shadow window preserves the qualification thresholds. A future
blocking role requires a new language-policy release, corpus, migration note,
and accountable approval; it stays outside this contract.

## Evaluation receipt and recovery

Each evaluated unit records:

- run identifier, timestamp, repository commit, path, span, and surface kind;
- input classification and SHA-256 digest;
- policy, model, prompt, response-schema, and runner coordinates;
- normalized advisory label, rationale, and output digest;
- reviewer disposition and adjudication status; and
- latency, retry count, and typed completion state.

Timeout, schema failure, coordinate drift, or unavailable inference produces
`shadow_unavailable`. The deterministic gate proceeds independently, and the
receipt routes the affected unit to ordinary author or human review.

Any privacy, egress, tool, write, delegation, or authority-boundary event moves
the reviewer to `inactive_design_contract`, preserves the evidence receipt, and
routes recovery through the accountable Security, Privacy, and language-policy
owners.

## Activation change set

A future activation change introduces the model and prompt coordinates, a
closed evaluation-manifest schema, a closed run-receipt schema, qualification
fixtures, conformance tests, retention configuration, and an explicitly
advisory workflow. The current release introduces documentation only and
creates zero runtime or continuous-integration integration.
