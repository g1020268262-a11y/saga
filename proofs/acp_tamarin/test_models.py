import unittest
import re
from pathlib import Path
from run_model import CASES, generate, matching_rules, finite_replay, expected, LEMMA_TYPES, checked_archive_bytes, blob

class ModelInputs(unittest.TestCase):
    def test_matching_order_and_scores(self):
        self.assertEqual(matching_rules('alice@example.com:agent', CASES['da']['rules']), [(70,-1),(0,10)])
        self.assertEqual(matching_rules('alice@example.com:agent', CASES['reverse']['rules']), [(0,10),(70,-1)])
        self.assertEqual(matching_rules('alice@example.com:agent',[{'pattern':'bob@example.com:*','budget':10}]),[])
        self.assertEqual(matching_rules('alice@example.com:agent',[{'pattern':'alice@example.com:agent','budget':10}]),[(108,10)])
    def test_all_models(self):
        for name, case in CASES.items():
            with self.subTest(case=name):
                theory=generate(name,case)
                self.assertNotRegex(theory,r'@[A-Z_]+@')
                self.assertEqual(set(re.findall(r'^lemma (\w+):',theory,re.M)),set(LEMMA_TYPES))
                self.assertIn('Scan0(sid,stage,best,current)',theory)
                self.assertIn('Scan1(sid,stage,best,',theory)
                self.assertEqual(len(re.findall(r'^rule (?:Spec_Select_Better|Impl_Select_Better|Skip_Rule)_\d+:',theory,re.M)),3*len(matching_rules('alice@example.com:agent',case['rules'])))
                self.assertEqual(theory.count('rule Setup:'),1)
                preview=finite_replay(case)
                self.assertEqual(preview['provider_budget'],case['observed'])
                self.assertEqual(preview['spec_budget'],case['spec'])
                self.assertEqual(preview['chat_accepted'],case['observed']>0)
                self.assertEqual(preview['chat_accepted'],expected(case)['chat_accept_reachable']['expected']=='verified')
    def test_da_counterexample_preview(self):
        e=finite_replay(CASES['da'])['events']
        spec=[x for x in e if x['event']=='SpecDecision'][0]
        self.assertEqual(spec['decision'],'deny')
        self.assertEqual([x['best_after'] for x in e if x.get('stage')=='provider'],[-1,-1])
        self.assertEqual([x['event'] for x in e][-4:],['TokenIssue','TokenReceive','ChatSend','ChatAccept'])
    def test_controls(self):
        for name in ('dd','reverse'):
            e=finite_replay(CASES[name])
            self.assertIsNone(e['receiver_budget'])
            self.assertEqual(e['events'][-1]['event'],'ProviderReject')
        self.assertTrue(finite_replay(CASES['aa'])['chat_accepted'])

    def test_observed_and_expected_values_do_not_enable_rules(self):
        for name,case in CASES.items():
            altered={**case,'spec':123,'observed':456}
            original=generate(name,case).split('lemma evaluation_reachable:',1)[0]
            changed=generate(name,altered).split('lemma evaluation_reachable:',1)[0]
            self.assertEqual(original,changed)

    def test_original_security_properties_preserved(self):
        folder=Path(__file__).resolve().parent
        original=(folder/'audit/initial-contact_policy.template.spthy').read_text(encoding='utf-8')
        current=(folder/'contact_policy.template.spthy').read_text(encoding='utf-8')
        self.assertEqual(original.split('lemma evaluation_reachable:',1)[1],current.split('lemma evaluation_reachable:',1)[1])

    def test_pinned_byte_encoding_fails_closed(self):
        historical=b'{"a":1}\n'
        self.assertEqual(checked_archive_bytes(historical.replace(b'\n',b'\r\n'),historical,blob(historical))['verified_encoding'],'uniform-CRLF')
        with self.assertRaises(ValueError): checked_archive_bytes(b'{"a":2}\n',historical,blob(historical))
        with self.assertRaises(ValueError): checked_archive_bytes(historical,historical,'0'*40)

if __name__=='__main__': unittest.main(verbosity=2)
