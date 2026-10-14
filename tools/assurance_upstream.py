"""Use upstream domain owners for one complete offline study assurance return."""
from __future__ import annotations

from typing import Mapping
from assurance_companion import AssuranceError, StudyAssessment, document


def receive_study(artifacts: Mapping[str, bytes]) -> StudyAssessment:
    """Recompute through the comparator owner and bind its complete result.

    Exact report equality is a receiving check, not an independent scientific
    oracle. The pack's authored expectations and accountable review retain
    their separate roles. Input sizes are bounded before these owner calls.
    """
    try:
        from lims_eln_contracts.administrative_study import admit_administrative_study
        from lims_eln_contracts.canonical import canonical_json_bytes, canonical_sha256
        from lims_eln_contracts.study_interpretation import interpret_administrative_study
        from lims_eln_sim.administrative_pack import admit_pack
        from comparative_evidence.administrative_evaluation import EvaluationReport, evaluate, demonstration_study
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.split(".")[0] in {"lims_eln_contracts", "lims_eln_sim", "comparative_evidence"}:
            raise AssuranceError("owner_environment", "Install the pinned assurance profile in an isolated environment.") from None
        raise
    try:
        pack = admit_pack(artifacts["pack"])
        study = admit_administrative_study(artifacts["study"])
        report = EvaluationReport.model_validate_json(artifacts["report"], strict=True)
        expected = evaluate(pack, study, evidence_mode=report.evidence_mode)
        if canonical_json_bytes(report) != canonical_json_bytes(expected):
            raise AssuranceError("report_consistency", "Return the report to its comparator owner with the same admitted pack and study.")
        if report.evidence_mode == "fixture_demonstration" and study != demonstration_study(pack):
            raise AssuranceError("fixture_identity", "Retain the exact demonstration identity or receive caller-supplied observations.")
        interpretation = interpret_administrative_study(study)
    except AssuranceError:
        raise
    except (ValueError, TypeError, KeyError, RecursionError):
        raise AssuranceError("upstream_admission", "Return the artifact to its typed source owner for admission and identity reconciliation.") from None
    comparison = interpretation.comparison
    bindings = {
        "source": pack.design.source_digest,
        "oracle": canonical_sha256([item.model_dump(mode="json", by_alias=True) for item in pack.expected]),
        "specification": canonical_sha256(study.specification),
        "execution": canonical_sha256(study.specification.expected_execution),
        "catalog": canonical_sha256(study.specification.catalog),
        "policy": canonical_sha256(study.specification.policy),
        "scoring": report.scoring_digest,
    }
    population = {key: getattr(comparison, key) for key in ("planned", "attempted", "completed", "pending", "abstained", "failed", "cancelled", "excluded")}
    population.update(usable=interpretation.usable_runs, scored=report.scored_coverage.numerator)
    return StudyAssessment(bindings, population, tuple(study.specification.factor_names), report.evidence_mode, report.scientific_oracle_disagreements)
