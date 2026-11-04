"""Issue 39 exercises use admitted source records and independent literal oracles."""
from __future__ import annotations

import copy
from importlib.util import find_spec
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from assurance_companion import (
    AssuranceError, DEPENDENCIES, digest, encoded, invalidate, receive,
    record_review, validate_record,
)
from validate_governance import SchemaValidator

AVAILABLE = all(find_spec(name) is not None for name in (
    'lims_eln_contracts', 'lims_eln_sim', 'comparative_evidence',
))


class RunbookRouteTests(unittest.TestCase):
    def test_owner_routes_and_lean_metadata(self):
        directory = ROOT / '.agents/runbooks'
        names = (
            'population-claim-review',
            'administrative-decision-assurance-and-recourse',
            'source-and-claim-invalidation',
            'governance-contract-handoff',
        )
        for name in names:
            path = directory / (name + '.v0.1.md')
            text = path.read_text()
            with self.subTest(runbook=name):
                self.assertTrue(text.startswith('---\n'))
                for field in ('title:', 'version: 0.1.0', 'status: working',
                              'audience:', 'source_band: public_possible', 'task_type:'):
                    self.assertIn(field, text.split('---', 2)[1])
                for heading in ('Entry and authority', 'Checks and exercise',
                                'Recovery and stopping event', 'Handback and acceptance event'):
                    self.assertIn('## ' + heading, text)
                self.assertIn('test_assurance_exercises.py', text)
        for path in (directory / 'index.md', *(directory / (n + '.v0.1.md') for n in names)):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in target and not target.startswith('#'):
                    with self.subTest(source=path.name, target=target):
                        self.assertTrue((path.parent / target.split('#', 1)[0]).is_file())


@unittest.skipUnless(AVAILABLE, 'Install requirements-assurance.txt for the source-owned exercises.')
class AdministrativeRunbookExercises(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from lims_eln_contracts.administrative_admission import (
            AdministrativeAdmissionLimits, admit_administrative_contract,
        )
        from lims_eln_contracts.canonical import canonical_json_bytes
        from lims_eln_contracts.resources import load_independent_multilabel_policy_example
        from lims_eln_sim.administrative_pack import build_pack
        from comparative_evidence.administrative_evaluation import demonstration_study

        cls.request = json.loads((ROOT / 'examples/assurance-request.json').read_text())
        cls.capability = (ROOT / 'examples/assurance-capability.json').read_bytes()
        cls.science_claim = json.loads((ROOT / 'examples/claim-veracity.json').read_text())
        cls.pack = build_pack(repeats=2)
        cls.study = demonstration_study(cls.pack)
        cls.domain = admit_administrative_contract(
            canonical_json_bytes(load_independent_multilabel_policy_example()),
            limits=AdministrativeAdmissionLimits(
                max_input_bytes=262144, max_json_depth=32, max_decoded_values=50000,
                max_records=128, max_provenance_edges=512, max_graph_steps=8192,
                max_output_bytes=262144,
            ),
        ).contract

    def packet(self, *, pack=None, study=None, mode='fixture_demonstration', statement=None):
        from lims_eln_contracts.canonical import canonical_json_bytes
        from comparative_evidence.administrative_evaluation import evaluate

        pack = self.pack if pack is None else pack
        study = self.study if study is None else study
        report = evaluate(pack, study, evidence_mode=mode)
        artifacts = {role: canonical_json_bytes(value) for role, value in (
            ('pack', pack), ('study', study), ('report', report),
        )}
        artifacts['capability'] = self.capability
        request = copy.deepcopy(self.request)
        request.update(
            companion_id='ASSURANCE-EXERCISE-001',
            intended_use='Review authored administrative outputs before choosing a further study.',
            omitted_dimensions=['Population prevalence', 'Real payer outcomes',
                                'Service effectiveness', 'Independent calibration'],
        )
        for role in ('pack', 'study', 'report'):
            request['artifacts'].append({
                'artifact_id': 'ARTIFACT-EXERCISE-' + role.upper(), 'role': role,
                'schema_id': json.loads(artifacts[role])['$schema'],
                'digest': digest(artifacts[role]),
                'source_commit': ('8c31ab403207c1797da0cb55b5aaee0cf690aa75' if role == 'pack'
                                  else '98093c2021dce604564592074b67307338e374f6'),
            })
        for claim_id, kind, text in (
            ('CLAIM-OUTPUT', 'output_comparison', statement or
             'The authored study retains four designed scientific-output disagreements.'),
            ('CLAIM-POPULATION', 'population_effect',
             'Assess whether these authored cohorts establish a population effect.'),
        ):
            request['claims'].append({
                'claim_id': claim_id, 'claim_type': kind, 'statement': text,
                'depends_on': sorted(DEPENDENCIES[kind]), 'review_state': 'pending',
                'evidence_ceiling': 'pending', 'review_note': 'Awaiting modeled review.',
            })
        return request, artifacts, report

    @staticmethod
    def claim(record, identity):
        return next(row for row in record['claims'] if row['claim_id'] == identity)

    def test_proposal_validation_override_and_recourse_keep_distinct_owners(self):
        from pydantic import ValidationError
        from lims_eln_contracts.external_administrative import AdministrativeDecision
        from lims_eln_contracts.resources import load_administrative_adapter_contract_example

        original = self.domain.model_dump_json()
        decisions = {row.decision_id: row for row in self.domain.administrative_decisions}
        final = decisions['DECISION-ADMIN-BASELINE-001']
        classification = next(row for row in self.domain.insurance_classifications
                              if row.classification_id == 'CLASS-INSURANCE-MULTI-001')
        self.assertEqual('Commercial + community support bridge', classification.raw_label)
        self.assertEqual(('insurance-category:commercial', 'insurance-category:supplemental'),
                         tuple(term.term_id for term in classification.assigned_terms))
        self.assertEqual('POLICY-SYNTHETIC-ROUTING-001', final.policy_evaluation.policy_rule_set_ref)
        self.assertEqual(('RULE-MULTILABEL-001', 'RULE-COMMERCIAL-ACTIVE-FALLBACK-001'),
                         final.policy_evaluation.matched_rule_refs)
        self.assertEqual('RULE-MULTILABEL-001', final.policy_evaluation.selected_rule_ref)
        proposal = final.model_dump(mode='json')
        proposal.update(decision_id='DECISION-EXERCISE-PROPOSAL', state='proposed', review=None,
                        transitions=proposal['transitions'][:1],
                        outcome=proposal['policy_evaluation']['outcome'])
        admitted = AdministrativeDecision.model_validate_json(encoded(proposal), strict=True)
        self.assertEqual('policy-outcome:manual_review', admitted.outcome.term_id)
        self.assertIsNone(admitted.review)
        self.assertEqual('policy-outcome:evidence_request', final.outcome.term_id)
        self.assertEqual('revise', final.review.disposition.value)
        self.assertNotEqual(final.actor.actor_id, final.review.reviewer_id)
        self.assertEqual('synthetic_only', final.effect.value)
        self.assertEqual('role:administrative_reviewer', final.recourse.owner_role.term_id)
        self.assertEqual('RECOURSE-SYNTHETIC-BASELINE-001', final.recourse.route_id)
        invalid = final.model_dump(mode='json')
        invalid['review'] = None
        with self.assertRaises(ValidationError):
            AdministrativeDecision.model_validate_json(encoded(invalid), strict=True)
        missing = decisions['DECISION-ADMIN-MISSING-INPUT-001']
        self.assertEqual('abstained', missing.policy_evaluation.state.value)
        self.assertEqual(('enrollment_state',), missing.policy_evaluation.missing_input_ids)
        self.assertIsNone(missing.policy_evaluation.selected_rule_ref)
        ai = next(row for row in self.domain.insurance_classifications
                  if row.classification_id == 'CLASS-INSURANCE-ABSTAIN-001')
        self.assertEqual('llm_proposal', ai.method.kind.value)
        self.assertEqual('abstained', ai.state.value)
        self.assertEqual('design_only', load_administrative_adapter_contract_example().execution_standing)
        self.assertEqual(original, self.domain.model_dump_json())

    def test_population_controls_omissions_and_held_scientific_interpretation(self):
        request, artifacts, report = self.packet()
        prior = receive(encoded(request), artifacts)
        self.assertEqual({'planned': 144, 'attempted': 136, 'completed': 128,
                          'usable': 128, 'scored': 128, 'pending': 4, 'abstained': 4,
                          'failed': 4, 'cancelled': 0, 'excluded': 4},
                         prior['assessment']['population'])
        self.assertEqual(['Population prevalence', 'Real payer outcomes',
                          'Service effectiveness', 'Independent calibration'], prior['omitted_dimensions'])
        observations = {row.run_id: row for row in self.study.observations}
        for case, expected in (('REPEAT', ('review', 'review', 10, 10)),
                               ('REPORTABILITY', ('review', 'submit', 10, 5))):
            with self.subTest(case=case):
                a, b = (observations[f'SYN-PAIR-{case}-ADULT-EN-0-{arm}'] for arm in ('a', 'b'))
                left, right = (json.loads(row.administrative_output.text) for row in (a, b))
                self.assertEqual(expected, (left['policy_state'], right['policy_state'],
                                            left['workflow_minutes'], right['workflow_minutes']))
                self.assertEqual(a.scientific_output.text, b.scientific_output.text)
                self.assertEqual(case == 'REPEAT', a.administrative_output.text == b.administrative_output.text)
                self.assertEqual('  Commercial  ', left['raw_label'])
        self.assertEqual(4, report.scientific_oracle_disagreements)
        snapshot = encoded(prior)
        reviewed = record_review(prior, claim_id='CLAIM-OUTPUT', successor_id='ASSURANCE-REVIEWED-002',
                                 note='The modeled review covers fixture outputs; service meaning remains with scientific review.')
        self.assertEqual('fixture_demonstration', self.claim(reviewed, 'CLAIM-OUTPUT')['evidence_ceiling'])
        self.assertEqual('held', self.claim(reviewed, 'CLAIM-POPULATION')['review_state'])
        with self.assertRaises(AssuranceError) as held:
            record_review(prior, claim_id='CLAIM-POPULATION', successor_id='ASSURANCE-HELD-002',
                          note='Receive representative population evidence first.')
        self.assertEqual('review_entry', held.exception.code)
        self.assertEqual(snapshot, encoded(prior))
        scientific = copy.deepcopy(self.science_claim)
        scientific.update(claim_id='CLAIM-SERVICE-OUTCOME-EXERCISE', claim_type='projected_outcome',
                          statement='The designed administrative difference improves service outcomes in a receiving population.',
                          status='local_measurement_needed', settlement_status='candidate', evidence_artifacts=[],
                          limitations=['Four injected fixture disagreements establish detector behavior.',
                                       'Service effectiveness and population representativeness require independent evidence.'])
        scientific['scope_band'].update(technology='Administrative fixture comparison', versions=['0.1.0'],
                                        environment='Offline synthetic exercise')
        scientific['provenance'] = [{'source_label': 'Authored synthetic comparison', 'source_kind': 'simulation',
                                     'locator': 'evidence://governance/exercises/administrative-comparison',
                                     'retrieved_on': '2026-10-14'}]
        scientific['verification'] = {'method': 'Receive independent scientific and population-use evidence.',
                                      'expected_observation': 'A named scientific reviewer assesses the intended service claim.',
                                      'checks': []}
        scientific['recheck_triggers'] = ['Independent service evidence or the intended population changes.']
        self.assertEqual([], SchemaValidator(ROOT / 'schemas/claim-veracity.schema.json').validate(scientific))
        self.assertEqual('local_measurement_needed', scientific['status'])
        missing = copy.deepcopy(request)
        missing['omitted_dimensions'] = []
        with self.assertRaises(AssuranceError) as omitted:
            receive(encoded(missing), artifacts)
        self.assertEqual('record_shape', omitted.exception.code)

    def test_small_cells_withhold_estimates_while_full_population_remains_visible(self):
        from lims_eln_contracts.canonical import canonical_json_bytes
        from lims_eln_sim.administrative_pack import admit_pack

        document = self.pack.model_dump(mode='json', by_alias=True)
        document['design']['minimum_subjects'] = 32
        pack = admit_pack(canonical_json_bytes(document))
        request, artifacts, report = self.packet(pack=pack)
        companion = receive(encoded(request), artifacts)
        group = next(row for row in report.groups if row.cohort == 'SYN-COHORT-ADULT-EN')
        self.assertEqual((72, 64, 28, 14), (group.planned_runs, group.scored_runs,
                                          group.complete_pairs, group.independent_subjects))
        self.assertEqual('small_cell', group.standing)
        self.assertIsNone(group.workflow_difference_minutes)
        empty = next(row for row in report.groups if row.cohort == 'SYN-COHORT-UNREPRESENTED')
        self.assertEqual(('empty', 0, 0), (empty.standing, empty.planned_runs, empty.independent_subjects))
        self.assertIsNone(empty.workflow_difference_minutes)
        self.assertEqual(144, companion['assessment']['population']['planned'])
        self.assertEqual(128, companion['assessment']['population']['scored'])
        self.assertEqual('held', self.claim(companion, 'CLAIM-POPULATION')['review_state'])

    def test_recourse_corrects_source_then_forms_a_fresh_review_successor(self):
        from lims_eln_contracts.administrative_study import admit_administrative_study
        from lims_eln_contracts.canonical import canonical_json_bytes, canonical_sha256

        original = canonical_json_bytes(self.study)
        document = self.study.model_dump(mode='json', by_alias=True)
        row = next(item for item in document['observations'] if item['run_id'] == 'SYN-PAIR-REPEAT-ADULT-EN-0-a')
        source = next(run for run in self.study.runs if run.run_id == row['run_id'])
        self.assertEqual('  Commercial  ', json.loads(source.administrative_input)['raw_label'])
        output = json.loads(row['administrative_output']['text'])
        output['raw_label'] = 'Commercial'
        text = canonical_json_bytes(output).decode()
        row.update(observation_id='SYN-OBS-RECOURSE-DISPUTED')
        row['administrative_output'].update(text=text, digest=canonical_sha256(text))
        disputed = admit_administrative_study(canonical_json_bytes(document))
        request, artifacts, report = self.packet(study=disputed, mode='caller_supplied_synthetic',
                                               statement='One observed output loses the source label spacing.')
        self.assertEqual((127, 128), (report.raw_preservation.numerator, report.raw_preservation.denominator))
        prior = receive(encoded(request), artifacts)
        prior_bytes, artifact_bytes = encoded(prior), dict(artifacts)
        held = invalidate(prior, changed_bindings=frozenset({'study', 'report'}),
                          successor_id='ASSURANCE-RECOURSE-002',
                          reason='The observation producer must restore the exact source label and recompute the report.')
        self.assertEqual('held', self.claim(held, 'CLAIM-OUTPUT')['review_state'])
        output['raw_label'] = '  Commercial  '
        text = canonical_json_bytes(output).decode()
        row.update(observation_id='SYN-OBS-RECOURSE-CORRECTED')
        row['administrative_output'].update(text=text, digest=canonical_sha256(text))
        corrected = admit_administrative_study(canonical_json_bytes(document))
        fresh_request, fresh_artifacts, corrected_report = self.packet(
            study=corrected, mode='caller_supplied_synthetic',
            statement='Corrected outputs preserve every scored raw label within this authored study.')
        fresh_request['companion_id'] = 'ASSURANCE-CORRECTED-003'
        fresh = receive(encoded(fresh_request), fresh_artifacts)
        reviewed = record_review(fresh, claim_id='CLAIM-OUTPUT', successor_id='ASSURANCE-CORRECTED-REVIEW-004',
                                 note='Modeled review receives the corrected observation and its recomputed report.')
        self.assertEqual((128, 128), (corrected_report.raw_preservation.numerator, corrected_report.raw_preservation.denominator))
        self.assertEqual(4, corrected_report.scientific_oracle_disagreements)
        self.assertIsNone(fresh['supersedes'])
        self.assertEqual('ASSURANCE-CORRECTED-003', reviewed['supersedes'])
        self.assertEqual(digest(encoded(fresh)), reviewed['prior_digest'])
        self.assertEqual(digest(prior_bytes), held['prior_digest'])
        self.assertNotEqual(prior['assessment']['bindings']['study'], fresh['assessment']['bindings']['study'])
        self.assertEqual(prior['assessment']['bindings']['policy'], fresh['assessment']['bindings']['policy'])
        self.assertEqual(prior_bytes, encoded(prior))
        self.assertEqual(artifact_bytes, artifacts)
        self.assertEqual(original, canonical_json_bytes(self.study))

    def test_policy_date_and_intended_use_changes_hold_their_own_dependents(self):
        request, artifacts, _ = self.packet()
        prior = receive(encoded(request), artifacts)
        prior = record_review(prior, claim_id='CLAIM-COMPOSITION-001', successor_id='ASSURANCE-COMPOSITION-002',
                              note='Review the declared composition within the local exercise.')
        prior = record_review(prior, claim_id='CLAIM-OUTPUT', successor_id='ASSURANCE-OUTPUT-003',
                              note='Review the authored output comparison within its fixture evidence.')
        snapshot = encoded(prior)
        row = next(item for item in self.study.observations if item.run_id == 'SYN-PAIR-DATE-ADULT-EN-0-b')
        run = next(item for item in self.study.runs if item.run_id == row.run_id)
        self.assertEqual('2027-01-01', json.loads(run.administrative_input)['service_day'])
        self.assertEqual('expired', json.loads(row.administrative_output.text)['policy_state'])
        policy = invalidate(prior, changed_bindings=frozenset({'policy'}), successor_id='ASSURANCE-POLICY-004',
                            reason='The policy owner proposes an effective window beginning 2026-10-02; receive its reviewed successor source.')
        self.assertEqual('held', self.claim(policy, 'CLAIM-OUTPUT')['review_state'])
        self.assertEqual('reviewed', self.claim(policy, 'CLAIM-COMPOSITION-001')['review_state'])
        changed_use = invalidate(prior, changed_bindings=frozenset({'intended_use'}), successor_id='ASSURANCE-USE-004',
                                 reason='The intended use changes from fixture review to service-use assessment.')
        self.assertEqual({'held'}, {claim['review_state'] for claim in changed_use['claims']})
        for changed in (policy, changed_use):
            validate_record(changed)
            self.assertEqual(digest(snapshot), changed['prior_digest'])
            self.assertEqual(prior['companion_id'], changed['supersedes'])
            self.assertEqual('pending', changed['assessment']['configured_execution'])
        self.assertEqual(snapshot, encoded(prior))


if __name__ == '__main__':
    unittest.main()
