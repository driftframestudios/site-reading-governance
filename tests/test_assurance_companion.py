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
        for mutation, code in ((lambda r: r['artifacts'].append(copy.deepcopy(r['artifacts'][0])), 'record_shape'), (lambda r: r['artifacts'][0].update(digest='sha256:'+'0'*64), 'artifact_digest'), (lambda r: r['artifacts'][0].update(schema_id='urn:unsupported:1'), 'artifact_schema'), (lambda r: r['claims'][0].update(depends_on=['capability']), 'claim_dependencies'), (lambda r: r['claims'][0].update(review_state='reviewed'), 'request_review')):
            with self.subTest(code=code):
                request=copy.deepcopy(self.request);mutation(request)
                with self.assertRaises(AssuranceError) as error: receive(encoded(request), self.artifacts)
                self.assertEqual(error.exception.code, code)

    def test_distinct_references_keep_role_and_identity_unique(self):
        for changes in ({'artifact_id': 'ARTIFACT-CAPABILITY-002'}, {'role': 'study'}):
            with self.subTest(changes=changes):
                request = copy.deepcopy(self.request)
                request['artifacts'].append({**request['artifacts'][0], **changes})
                with self.assertRaises(AssuranceError) as error:
                    receive(encoded(request), self.artifacts)
                self.assertEqual(error.exception.code, 'duplicate_reference')

    def test_companion_readmission_reconciles_binding_and_claim_support(self):
        mutations = (
            ('intended-use', lambda r: r.update(intended_use='A changed receiving decision.'), 'assessment_binding'),
            ('missing-binding', lambda r: r['assessment']['bindings'].pop('capability'), 'assessment_bindings'),
            ('artifact-digest', lambda r: r['artifacts'][0].update(digest='sha256:' + '0' * 64), 'assessment_binding'),
            ('extra-binding', lambda r: r['assessment']['bindings'].update(policy='sha256:' + '0' * 64), 'assessment_bindings'),
            ('unsupported-claim', lambda r: r['claims'][0].update(claim_type='output_comparison', depends_on=sorted(DEPENDENCIES['output_comparison'])), 'claim_support'),
        )
        for name, mutation, code in mutations:
            for transition in ('validate', 'review', 'invalidate'):
                with self.subTest(mutation=name, transition=transition):
                    record = self.accepted()
                    mutation(record)
                    snapshot = encoded(record)
                    with self.assertRaises(AssuranceError) as error:
                        if transition == 'validate':
                            validate_record(record)
                        elif transition == 'review':
                            record_review(record, claim_id='CLAIM-COMPOSITION-001', successor_id='ASSURANCE-REVIEW-002', note='A scoped review.')
                        else:
                            invalidate(record, changed_bindings=frozenset({'policy'}), successor_id='ASSURANCE-CHANGE-002', reason='Receive the current policy.')
                    self.assertEqual(error.exception.code, code)
                    self.assertEqual(encoded(record), snapshot)

    def test_invalidated_claim_stays_held_until_fresh_admission(self):
        held = invalidate(self.accepted(), changed_bindings=frozenset({'intended_use'}), successor_id='ASSURANCE-CHANGE-002', reason='Receive evidence for the revised use.')
        for state in ('review_ready', 'reviewed'):
            with self.subTest(state=state):
                altered = copy.deepcopy(held)
                altered['claims'][0]['review_state'] = state
                with self.assertRaises(AssuranceError) as error:
                    validate_record(altered)
                self.assertEqual(error.exception.code, 'claim_invalidation')

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

    def test_successors_preserve_known_identity_and_prior_records(self):
        prior = self.accepted()
        prior_bytes = encoded(prior)
        reviewed = record_review(
            prior, claim_id='CLAIM-COMPOSITION-001', successor_id='ASSURANCE-REVIEW-002',
            note='Review the composition within its supplied evidence.',
        )
        reviewed_bytes = encoded(reviewed)
        for reused_id in (prior['companion_id'], reviewed['companion_id']):
            with self.subTest(reused_id=reused_id), self.assertRaises(AssuranceError) as error:
                invalidate(reviewed, changed_bindings=frozenset({'intended_use'}),
                           successor_id=reused_id, reason='Receive the revised intended use.')
            self.assertEqual(error.exception.code, 'successor_identity')
        unchanged = invalidate(prior, changed_bindings=frozenset({'policy'}),
                               successor_id='ASSURANCE-POLICY-002', reason='Receive the changed policy.')
        unchanged_bytes = encoded(unchanged)
        with self.assertRaises(AssuranceError) as error:
            record_review(unchanged, claim_id='CLAIM-COMPOSITION-001',
                          successor_id=prior['companion_id'], note='Review the retained composition.')
        self.assertEqual(error.exception.code, 'successor_identity')
        successor = invalidate(reviewed, changed_bindings=frozenset({'intended_use'}),
                               successor_id='ASSURANCE-CHANGE-003', reason='Receive the revised intended use.')
        self.assertEqual(successor['supersedes'], reviewed['companion_id'])
        self.assertEqual(successor['prior_digest'], digest(reviewed_bytes))
        self.assertEqual(encoded(prior), prior_bytes)
        self.assertEqual(encoded(reviewed), reviewed_bytes)
        self.assertEqual(encoded(unchanged), unchanged_bytes)

    def test_escaped_surrogates_receive_typed_json_recovery(self):
        for scalar in ('\ud800', '\udfff'):
            mutations = (
                lambda r: r.update(intended_use='Review ' + scalar),
                lambda r: r['claims'][0].update(statement='Claim ' + scalar),
                lambda r: r['reviewer'].update(display_name='Reviewer ' + scalar),
                lambda r: r['reviewer'].update({scalar: 'value'}),
            )
            for index, mutation in enumerate(mutations):
                with self.subTest(scalar=repr(scalar), field=index):
                    request = copy.deepcopy(self.request)
                    mutation(request)
                    payload = json.dumps(request, ensure_ascii=True).encode('ascii')
                    with self.assertRaises(AssuranceError) as error:
                        receive(payload, self.artifacts)
                    self.assertEqual(error.exception.code, 'input_json')
            with self.subTest(scalar=repr(scalar), field='artifact-key'):
                artifact = json.loads(self.artifacts['capability'])
                artifact[scalar] = 'value'
                payload = json.dumps(artifact, ensure_ascii=True).encode('ascii')
                request = copy.deepcopy(self.request)
                request['artifacts'][0]['digest'] = digest(payload)
                with self.assertRaises(AssuranceError) as error:
                    receive(encoded(request), {'capability': payload})
                self.assertEqual(error.exception.code, 'input_json')

    def test_direct_records_and_successor_text_require_unicode_scalars(self):
        for scalar in ('\ud800', '\udfff'):
            prior = self.accepted()
            snapshot = encoded(prior)
            for transition in ('validate', 'review', 'invalidate'):
                with self.subTest(scalar=repr(scalar), transition=transition):
                    with self.assertRaises(AssuranceError) as error:
                        if transition == 'validate':
                            altered = copy.deepcopy(prior)
                            altered['claims'][0]['statement'] += scalar
                            validate_record(altered)
                        elif transition == 'review':
                            record_review(prior, claim_id='CLAIM-COMPOSITION-001', successor_id='ASSURANCE-REVIEW-002', note='Review ' + scalar)
                        else:
                            invalidate(prior, changed_bindings=frozenset({'intended_use'}), successor_id='ASSURANCE-CHANGE-002', reason='Changed ' + scalar)
                    self.assertEqual(error.exception.code, 'record_shape')
                    self.assertEqual(encoded(prior), snapshot)

    def test_unicode_text_preserves_exact_encoding_across_transitions(self):
        text = 'Review café, cafe\u0301, and \U0001f9ea.'
        self.request['intended_use'] = text
        self.request['claims'][0]['statement'] = text
        self.request['reviewer']['display_name'] = text
        # The escaped supplementary pair and literal UTF-8 produce the same text.
        prior = receive(json.dumps(self.request, ensure_ascii=True).encode('ascii'), self.artifacts)
        self.assertEqual(prior, self.accepted())
        self.assertEqual(prior['assessment']['bindings']['intended_use'], digest(text.encode('utf-8')))
        reviewed = record_review(prior, claim_id='CLAIM-COMPOSITION-001', successor_id='ASSURANCE-REVIEW-002', note=text)
        changed = invalidate(reviewed, changed_bindings=frozenset({'intended_use'}), successor_id='ASSURANCE-CHANGE-003', reason=text)
        self.assertEqual(reviewed['prior_digest'], digest(encoded(prior)))
        self.assertEqual(changed['prior_digest'], digest(encoded(reviewed)))
        self.assertEqual(reviewed['claims'][0]['review_note'], text)
        self.assertEqual(changed['change']['reason'], text)
        for record in (prior, reviewed, changed):
            self.assertEqual(json.loads(encoded(record)), record)
            self.assertIn(text, render_markdown(record))

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
