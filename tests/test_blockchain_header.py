import json
import copy
import hashlib
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRACTICE = ROOT / 'public/practice/crypto-forensics'
SCRIPT = PRACTICE / 'blockchain_header.py'


class BlockchainHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('blockchain_header', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.genesis = json.loads((PRACTICE / 'genesis-proof.json').read_text('utf-8'))

    def test_public_genesis_vector_and_explicit_verification_boundary(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(PRACTICE / 'genesis-proof.json')],
            capture_output=True, text=True, encoding='utf-8', check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['block_hash'], '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
        self.assertEqual(output['header']['timestamp_utc'], '2009-01-03T18:15:05Z')
        self.assertTrue(output['matches_bitcoin_mainnet_genesis'])
        self.assertTrue(output['pow_matches_claimed_target'])
        self.assertTrue(output['merkle_inclusion_matches_header'])
        self.assertFalse(output['active_chain_checked'])
        self.assertFalse(output['transaction_validity_checked'])
        self.assertFalse(output['ownership_checked'])
        self.assertIsNone(output['confirmations'])

    def test_reversed_display_txid_does_not_match_merkle_root(self):
        data = copy.deepcopy(self.genesis)
        data['target_txid'] = bytes.fromhex(data['target_txid'])[::-1].hex()
        self.assertFalse(self.module.analyze(data)['merkle_inclusion_matches_header'])

    def test_header_bit_change_breaks_known_block_reference(self):
        data = copy.deepcopy(self.genesis)
        header = bytearray.fromhex(data['header_hex'])
        header[-1] ^= 1
        data['header_hex'] = header.hex()
        result = self.module.analyze(data)
        self.assertFalse(result['matches_bitcoin_mainnet_genesis'])
        self.assertNotEqual(result['block_hash'], self.module.GENESIS)

    def test_three_leaf_branch_uses_internal_byte_order_and_odd_duplication(self):
        data = json.loads((PRACTICE / 'constructed-merkle-proof.json').read_text('utf-8'))
        result = self.module.analyze(data)
        self.assertTrue(result['merkle_inclusion_matches_header'])
        self.assertEqual(len(result['merkle_steps']), 2)
        self.assertTrue(result['merkle_steps'][0]['duplicated_last_node'])
        self.assertEqual(result['merkle_steps'][1]['sibling_side'], 'left')
        self.assertFalse(result['matches_bitcoin_mainnet_genesis'])

    def test_unpaired_node_cannot_use_arbitrary_sibling(self):
        data = json.loads((PRACTICE / 'constructed-merkle-proof.json').read_text('utf-8'))
        data['siblings'][0] = '00' * 32
        with self.assertRaisesRegex(ValueError, 'duplicate itself'):
            self.module.analyze(data)

    def test_duplicate_leaf_ambiguity_does_not_independently_prove_leaf_count(self):
        data = json.loads((PRACTICE / 'constructed-merkle-proof.json').read_text('utf-8'))
        three = self.module.analyze(data)
        data['transaction_count'] = 4
        four = self.module.analyze(data)
        self.assertTrue(three['merkle_inclusion_matches_header'])
        self.assertTrue(four['merkle_inclusion_matches_header'])
        self.assertFalse(four['leaf_count_independently_checked'])
        self.assertFalse(four['transaction_validity_checked'])

    def test_supplied_leaf_count_and_path_length_must_agree(self):
        data = copy.deepcopy(self.genesis)
        data['transaction_count'] = 3
        with self.assertRaisesRegex(ValueError, 'path length'):
            self.module.analyze(data)

    def test_booleans_are_not_transaction_indices(self):
        data = copy.deepcopy(self.genesis)
        data['transaction_index'] = False
        with self.assertRaisesRegex(ValueError, 'transaction_index'):
            self.module.analyze(data)

    def test_compact_targets_reject_sign_zero_and_overflow(self):
        for bits in [0x1d80ffff, 0, 0x23000001]:
            with self.subTest(bits=bits), self.assertRaises(ValueError):
                self.module.compact_target(bits)

    def test_header_must_be_exactly_eighty_bytes(self):
        data = copy.deepcopy(self.genesis)
        data['header_hex'] += '00'
        with self.assertRaisesRegex(ValueError, '80 bytes'):
            self.module.analyze(data)

    def test_easy_claimed_target_does_not_prove_mainnet_difficulty_or_membership(self):
        data = copy.deepcopy(self.genesis)
        header = bytearray.fromhex(data['header_hex'])
        header[72:76] = (0x207fffff).to_bytes(4, 'little')
        for nonce in range(100):
            header[76:80] = nonce.to_bytes(4, 'little')
            data['header_hex'] = header.hex()
            result = self.module.analyze(data)
            if result['pow_matches_claimed_target']:
                break
        self.assertTrue(result['pow_matches_claimed_target'])
        self.assertTrue(result['merkle_inclusion_matches_header'])
        self.assertFalse(result['matches_bitcoin_mainnet_genesis'])
        self.assertFalse(result['difficulty_rules_checked'])
        self.assertFalse(result['active_chain_checked'])

    def test_read_only_cli_does_not_modify_input(self):
        path = PRACTICE / 'genesis-proof.json'
        before = hashlib.sha256(path.read_bytes()).digest()
        result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)


if __name__ == '__main__':
    unittest.main()
