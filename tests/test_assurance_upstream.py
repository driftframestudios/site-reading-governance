"""Exercise real upstream admission when the optional study profile is present."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from assurance_companion import AssuranceError, DEPENDENCIES, digest, encoded, receive, invalidate

AVAILABLE=all(importlib.util.find_spec(name) is not None for name in ('lims_eln_contracts','lims_eln_sim','comparative_evidence'))


@unittest.skipUnless(AVAILABLE,'Install requirements-assurance.txt to exercise the real upstream owners.')
class UpstreamAssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from lims_eln_sim.administrative_pack import build_pack
        from comparative_evidence.administrative_evaluation import demonstration_study,evaluate
        from lims_eln_contracts.canonical import canonical_json_bytes
        cls.pack=build_pack();cls.study=demonstration_study(cls.pack)
        cls.report=evaluate(cls.pack,cls.study,evidence_mode='fixture_demonstration')
        cls.base={role:canonical_json_bytes(value) for role,value in (('pack',cls.pack),('study',cls.study),('report',cls.report))}

    def inputs(self):
        request=json.loads((ROOT/'examples/assurance-request.json').read_text())
        artifacts=dict(self.base)
        request['artifacts']=[{'artifact_id':'ARTIFACT-'+role.upper()+'-001','role':role,'schema_id':json.loads(data)['$schema'],'digest':digest(data),'source_commit':{'pack':'8c31ab403207c1797da0cb55b5aaee0cf690aa75','study':'83a97deb76b9a5636cc7da484d350d5556c51661','report':'98093c2021dce604564592074b67307338e374f6'}[role]} for role,data in artifacts.items()]
        request['claims']=[{'claim_id':'CLAIM-STUDY-001','claim_type':'output_comparison','statement':'The authored study preserves four designed scientific-output disagreements.','depends_on':sorted(DEPENDENCIES['output_comparison']),'review_state':'pending','evidence_ceiling':'pending','review_note':'Awaiting modeled review.'}]
        return request,artifacts

    def test_complete_population_and_named_identity_oracles(self):
        import hashlib
        from assurance_companion import validate_record
        request, artifacts = self.inputs()
        companion = receive(encoded(request), artifacts)
        self.assertEqual(companion['assessment']['population'], {
            'planned': 144, 'attempted': 136, 'completed': 128, 'pending': 4,
            'abstained': 4, 'failed': 4, 'cancelled': 0, 'excluded': 4,
            'usable': 128, 'scored': 128,
        })
        def sha(payload):
            return 'sha256:' + hashlib.sha256(payload).hexdigest()
        def canonical(value):
            return json.dumps(value, ensure_ascii=False, allow_nan=False,
                              sort_keys=True, separators=(',', ':')).encode('utf-8')
        expected = {role: sha(payload) for role, payload in artifacts.items()}
        expected.update({
            'intended_use': sha(request['intended_use'].encode('utf-8')),
            'source': self.pack.design.source_digest,
            'oracle': sha(canonical([entry.model_dump(mode='json', by_alias=True) for entry in self.pack.expected])),
            'specification': sha(canonical(self.study.specification.model_dump(mode='json', by_alias=True))),
            'execution': sha(canonical(self.study.specification.expected_execution.model_dump(mode='json', by_alias=True))),
            'catalog': sha(canonical(self.study.specification.catalog.model_dump(mode='json', by_alias=True))),
            'policy': sha(canonical(self.study.specification.policy.model_dump(mode='json', by_alias=True))),
            'scoring': self.report.scoring_digest,
        })
        self.assertEqual(set(expected), {'pack', 'study', 'report', 'intended_use', 'source', 'oracle', 'specification', 'execution', 'catalog', 'policy', 'scoring'})
        self.assertEqual(companion['assessment']['bindings'], expected)
        self.assertEqual(companion['assessment']['represented_dimensions'], ['age_band', 'language', 'reportability'])
        validate_record(json.loads(encoded(companion)))

    def test_observation_free_study_retains_planning_and_holds_output_claim(self):
        import importlib
        from assurance_companion import record_review, validate_record
        evaluate = importlib.import_module(type(self.report).__module__).evaluate
        planning = self.pack.study
        report = evaluate(self.pack, planning, evidence_mode='caller_supplied_synthetic')
        request, artifacts = self.inputs()
        artifacts['study'] = encoded(planning.model_dump(mode='json', by_alias=True))
        artifacts['report'] = encoded(report.model_dump(mode='json', by_alias=True))
        for reference in request['artifacts']:
            reference['digest'] = digest(artifacts[reference['role']])
        companion = receive(encoded(request), artifacts)
        self.assertEqual(companion['assessment']['population'], {
            'planned': 144, 'attempted': 0, 'completed': 0, 'pending': 144,
            'abstained': 0, 'failed': 0, 'cancelled': 0, 'excluded': 0,
            'usable': 0, 'scored': 0,
        })
        self.assertEqual(companion['assessment']['evidence_class'], 'caller_supplied_synthetic')
        self.assertEqual(companion['claims'][0]['review_state'], 'held')
        self.assertEqual(companion['claims'][0]['evidence_ceiling'], 'pending')
        with self.assertRaises(AssuranceError) as error:
            record_review(companion, claim_id=companion['claims'][0]['claim_id'], successor_id='ASSURANCE-EMPTY-REVIEW', note='Receive completed observations first.')
        self.assertEqual(error.exception.code, 'review_entry')
        companion['claims'][0]['review_state'] = 'review_ready'
        companion['claims'][0]['evidence_ceiling'] = 'caller_supplied_synthetic'
        with self.assertRaises(AssuranceError) as error:
            validate_record(companion)
        self.assertEqual(error.exception.code, 'claim_support')

    def test_review_and_invalidation_preserve_raw_inputs_and_prior_records(self):
        from assurance_companion import DEPENDENCIES, record_review, validate_record
        request, artifacts = self.inputs()
        request['intended_use'] = 'Review the designed offline comparison before choosing a further study.'
        population_claim = dict(request['claims'][0], claim_id='CLAIM-POPULATION-001',
                                claim_type='population_effect',
                                depends_on=sorted(DEPENDENCIES['population_effect']),
                                statement='Assess whether the designed cohorts establish a population effect.')
        request['claims'].append(population_claim)
        original_bytes = dict(artifacts)
        original_input = next(run.administrative_input for run in self.study.runs if run.run_id == 'SYN-PAIR-REPEAT-ADULT-EN-0-a')
        observation = next(item for item in self.study.observations if item.run_id == 'SYN-PAIR-REPEAT-ADULT-EN-0-a')
        self.assertIn('  Commercial  ', original_input)
        self.assertEqual(json.loads(observation.administrative_output.text)['raw_label'], '  Commercial  ')
        prior = receive(encoded(request), artifacts)
        snapshot = encoded(prior)
        self.assertEqual([claim['review_state'] for claim in prior['claims']], ['review_ready', 'held'])
        reviewed = record_review(prior, claim_id=prior['claims'][0]['claim_id'], successor_id='ASSURANCE-STUDY-REVIEW', note='The modeled reviewer accepts the fixture-level comparison; population interpretation receives its own evidence.')
        self.assertEqual(reviewed['claims'][0]['evidence_ceiling'], 'fixture_demonstration')
        self.assertEqual(reviewed['claims'][1]['review_state'], 'held')
        self.assertEqual(reviewed['prior_digest'], digest(snapshot))
        reviewed_snapshot = encoded(reviewed)
        for binding in ('policy', 'intended_use'):
            with self.subTest(binding=binding):
                held = invalidate(reviewed, changed_bindings=frozenset({binding}), successor_id='ASSURANCE-STUDY-CHANGE', reason='Receive the changed source and a fresh scoped review.')
                self.assertEqual([claim['review_state'] for claim in held['claims']], ['held', 'held'])
                self.assertEqual(held['supersedes'], reviewed['companion_id'])
                self.assertEqual(held['prior_digest'], digest(reviewed_snapshot))
                validate_record(held)
        self.assertEqual(encoded(prior), snapshot)
        self.assertEqual(encoded(reviewed), reviewed_snapshot)
        self.assertEqual(artifacts, original_bytes)
        self.assertEqual(next(run.administrative_input for run in self.study.runs if run.run_id == 'SYN-PAIR-REPEAT-ADULT-EN-0-a'), original_input)

    def test_complete_nonempty_population_and_fixture_ceiling(self):
        request,artifacts=self.inputs();result=receive(encoded(request),artifacts)
        self.assertEqual(result['assessment']['population']['planned'],144)
        self.assertEqual(result['assessment']['population']['scored'],128)
        self.assertEqual(result['assessment']['scientific_disagreements'],4)
        self.assertEqual(result['claims'][0]['evidence_ceiling'],'fixture_demonstration')
        self.assertEqual(len(result['assessment']['bindings']),11)
        self.assertEqual(result['claims'][0]['review_state'],'review_ready')

    def test_report_and_source_counterexamples(self):
        cases=[('report',lambda x:x.update(planned_runs=0)),('report',lambda x:x.update(scoring_digest='sha256:'+'0'*64)),('pack',lambda x:x['design'].update(source_digest='sha256:'+'0'*64)),('pack',lambda x:x['expected'][0].update(workflow_minutes=1439)),('study',lambda x:x.update(runs=[])),('study',lambda x:x['specification']['policy'].update(digest='sha256:'+'0'*64))]
        for role,mutate in cases:
            with self.subTest(role=role,mutation=mutate):
                request,artifacts=self.inputs();value=json.loads(artifacts[role]);mutate(value);artifacts[role]=encoded(value)
                next(r for r in request['artifacts'] if r['role']==role)['digest']=digest(artifacts[role])
                with self.assertRaises(AssuranceError):receive(encoded(request),artifacts)

    def test_mixed_execution_identity(self):
        request,artifacts=self.inputs();study=json.loads(artifacts['study'])
        row=next(x for x in study['observations'] if x.get('execution'))
        row['execution']['model_id']='other-fixture-model';artifacts['study']=encoded(study)
        next(x for x in request['artifacts'] if x['role']=='study')['digest']=digest(artifacts['study'])
        with self.assertRaises(AssuranceError):receive(encoded(request),artifacts)

    def test_partial_study_family(self):
        request,artifacts=self.inputs();request['artifacts']=request['artifacts'][:1];artifacts={'pack':artifacts['pack']}
        with self.assertRaises(AssuranceError) as error:receive(encoded(request),artifacts)
        self.assertEqual(error.exception.code,'study_membership')

    def test_policy_correction_holds_affected_claim(self):
        request,artifacts=self.inputs();prior=receive(encoded(request),artifacts)
        successor=invalidate(prior,changed_bindings=frozenset({'policy'}),successor_id='ASSURANCE-POLICY-002',reason='Receive the corrected effective policy and its recomputed report.')
        self.assertEqual(successor['claims'][0]['review_state'],'held')
        self.assertEqual(prior['claims'][0]['review_state'],'review_ready')


if __name__=='__main__':unittest.main()
