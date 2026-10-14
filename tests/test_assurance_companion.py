"""Focused receiving, scoped review, and immutable-recovery examples."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from assurance_companion import AssuranceError, DEPENDENCIES, digest, encoded, invalidate, receive, record_review, render_markdown, validate_record


class AssuranceCompanionTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / 'examples/assurance-request.json').read_text())
        self.artifacts = {'capability': (ROOT / 'examples/assurance-capability.json').read_bytes()}

    def accepted(self):
        return receive(encoded(self.request), self.artifacts)

    def test_capability_example_and_execution_ceiling(self):
        result = self.accepted()
        self.assertEqual(result, json.loads((ROOT / 'examples/administrative-assurance.json').read_text()))
        self.assertEqual(result['assessment']['configured_execution'], 'pending')
        self.assertIsNone(result['assessment']['population'])
        self.assertEqual([c['review_state'] for c in result['claims']], ['review_ready', 'held'])

    def test_reference_boundaries(self):
        for mutation, code in ((lambda r: r['artifacts'].append(copy.deepcopy(r['artifacts'][0])), 'duplicate_reference'), (lambda r: r['artifacts'][0].update(digest='sha256:'+'0'*64), 'artifact_digest'), (lambda r: r['artifacts'][0].update(schema_id='urn:unsupported:1'), 'artifact_schema'), (lambda r: r['claims'][0].update(depends_on=['capability']), 'claim_dependencies'), (lambda r: r['claims'][0].update(review_state='reviewed'), 'request_review')):
            with self.subTest(code=code):
                request=copy.deepcopy(self.request);mutation(request)
                with self.assertRaises(AssuranceError) as error: receive(encoded(request), self.artifacts)
                self.assertEqual(error.exception.code, code)

    def test_exact_membership_and_strict_json(self):
        for artifacts in ({}, {**self.artifacts,'study':b'{}'}):
            with self.assertRaises(AssuranceError) as error: receive(encoded(self.request), artifacts)
            self.assertEqual(error.exception.code,'artifact_membership')
        for payload in (b'[]',b'{"a":1,"a":2}',b'{"x":NaN}',b'\xff'):
            with self.subTest(payload=payload),self.assertRaises(AssuranceError): receive(payload,{})

    def test_review_preserves_prior_and_evidence_ceiling(self):
        prior=self.accepted();snapshot=encoded(prior)
        successor=record_review(prior,claim_id='CLAIM-COMPOSITION-001',successor_id='ASSURANCE-REVIEW-002',note='The modeled reviewer accepts the declared-composition statement for this local exercise.')
        self.assertEqual(encoded(prior),snapshot)
        self.assertEqual(successor['prior_digest'],digest(snapshot))
        self.assertEqual(successor['claims'][0]['evidence_ceiling'],'composition_only')
        self.assertEqual(successor['claims'][0]['review_state'],'reviewed')
        with self.assertRaises(AssuranceError): record_review(prior,claim_id='CLAIM-EXECUTION-001',successor_id='ASSURANCE-REVIEW-003',note='Review request')

    def test_policy_change_preserves_unaffected_composition(self):
        prior=self.accepted()
        successor=invalidate(prior,changed_bindings=frozenset({'policy'}),successor_id='ASSURANCE-CHANGE-002',reason='The source policy effective window changed; study claims receive fresh admission.')
        self.assertEqual(successor['claims'][0]['review_state'],'review_ready')
        changed=invalidate(prior,changed_bindings=frozenset({'intended_use'}),successor_id='ASSURANCE-CHANGE-003',reason='The receiving intended use changed; review the affected statements again.')
        self.assertEqual([c['review_state'] for c in changed['claims']],['held','held'])
        self.assertEqual(prior['claims'][0]['review_state'],'review_ready')

    def test_literal_safe_markdown(self):
        result=self.accepted();result['claims'][0]['statement']='A literal ``` sequence stays data.'
        rendered=render_markdown(result)
        self.assertIn('````json\n',rendered)
        self.assertTrue(rendered.endswith('````\n'))

    def test_forged_execution_acceptance_is_held(self):
        result=self.accepted();result['claims'][1]['review_state']='reviewed'
        with self.assertRaises(AssuranceError) as error: validate_record(result)
        self.assertEqual(error.exception.code,'claim_ceiling')


if __name__ == '__main__': unittest.main()
