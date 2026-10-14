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
        request['artifacts']=[{'artifact_id':'ARTIFACT-'+role.upper()+'-001','role':role,'schema_id':json.loads(data)['$schema'],'digest':digest(data),'source_commit':{'pack':'8c31ab403207c1797da0cb55b5aaee0cf690aa75','study':'83a97deb76b9a5636cc7da484d350d5556c51661','report':'47be93b7539b98df87bcd5530683efe90f7a7713'}[role]} for role,data in artifacts.items()]
        request['claims']=[{'claim_id':'CLAIM-STUDY-001','claim_type':'output_comparison','statement':'The authored study preserves four designed scientific-output disagreements.','depends_on':sorted(DEPENDENCIES['output_comparison']),'review_state':'pending','evidence_ceiling':'pending','review_note':'Awaiting modeled review.'}]
        return request,artifacts

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
