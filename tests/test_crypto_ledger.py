import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
SCRIPT = SITE/'public/practice/crypto-forensics/crypto_ledger.py'
spec = importlib.util.spec_from_file_location('crypto_ledger', SCRIPT)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class CryptoLedgerTests(unittest.TestCase):
    def audit(self, rows, target='TARGET', start=None, end=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input.csv'
            with path.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=ledger.FIELDS)
                writer.writeheader(); writer.writerows(rows)
            return ledger.analyze(path, target, start, end)

    def row(self, **changes):
        return {'source_ref': 'r1', 'source_kind': 'chain', 'chain': 'demo', 'asset_id': 'token:K',
                'decimals': '6', 'tx_hash': 'synthetic-t1', 'event_index': '0', 'block_hash': 'synthetic-b1',
                'event_type': 'transfer', 'from': 'ALICE', 'to': 'TARGET',
                'status': 'confirmed_success', 'raw_amount': '25000000',
                'timestamp_utc': '2026-01-01T00:00:00Z', **changes}

    def test_multiple_events_large_integers_and_asset_isolation(self):
        huge = 2**100 + 1
        rows = [self.row(), self.row(event_index='1', raw_amount='5000000'),
                self.row(chain='other'), self.row(asset_id='token:FAKE'),
                self.row(asset_id='native', decimals='18', raw_amount=str(huge))]
        summary, _, _ = self.audit(rows)
        groups = {(g['chain'], g['asset_id']): g for g in summary['groups']}
        self.assertEqual(groups[('demo', 'token:K')]['incoming_raw'], '30000000')
        self.assertEqual(groups[('demo', 'native')]['incoming_raw'], str(huge))
        self.assertEqual(groups[('demo', 'native')]['incoming'], '1267650600228.229401496703205377')
        self.assertEqual(len(groups), 4)

    def test_duplicates_conflicts_and_updates_require_review(self):
        rows = [self.row(), self.row(source_ref='page2'),
                self.row(tx_hash='c1', raw_amount='100'), self.row(tx_hash='c1', raw_amount='200'),
                self.row(tx_hash='c2', status='pending'), self.row(tx_hash='c2')]
        summary, decisions, issues = self.audit(rows)
        self.assertEqual(summary['groups'][0]['incoming_raw'], '25000000')
        self.assertEqual(summary['decisions'], {'conflict': 4, 'duplicate': 1, 'incoming': 1})
        self.assertEqual(len(issues), 4)
        self.assertEqual(summary['review_status'], 'needs_review')

    def test_failures_approval_self_platform_and_fees_are_separate(self):
        rows = [self.row(), self.row(tx_hash='out', **{'from': 'TARGET', 'to': 'BOB'}, raw_amount='3000000'),
                self.row(tx_hash='fee', event_type='fee', **{'from': 'TARGET', 'to': 'FEE'}, raw_amount='2000'),
                self.row(tx_hash='failed-fee', event_type='fee', status='confirmed_failed', **{'from': 'TARGET', 'to': 'FEE'}, raw_amount='1000'),
                self.row(tx_hash='zero', raw_amount='0'), self.row(tx_hash='self', **{'from': 'TARGET'}),
                self.row(tx_hash='failed', status='confirmed_failed'), self.row(tx_hash='pending', status='pending'),
                self.row(tx_hash='reorg', status='orphaned'), self.row(tx_hash='approval', event_type='approval'),
                self.row(tx_hash='p', source_kind='platform', block_hash='')]
        summary, _, _ = self.audit(rows)
        group = summary['groups'][0]
        self.assertEqual(group['net_flow_raw'], '21997000')
        self.assertEqual(group['incoming_events'], 2)
        self.assertEqual(group['positive_incoming_events'], 1)
        self.assertEqual(summary['decisions']['platform_separate'], 1)

    def test_half_open_time_and_explicit_timezone(self):
        rows = [self.row(), self.row(tx_hash='end', timestamp_utc='2026-01-02T00:00:00Z'),
                self.row(tx_hash='same', timestamp_utc='2026-01-01T08:00:00+08:00'),
                self.row(tx_hash='naive', timestamp_utc='2026-01-01T00:00:00')]
        summary, _, issues = self.audit(rows, start='2026-01-01T00:00:00Z', end='2026-01-02T00:00:00Z')
        self.assertEqual(summary['groups'][0]['incoming_raw'], '50000000')
        self.assertEqual(summary['decisions']['outside_time'], 1)
        self.assertEqual(len(issues), 1)

    def test_invalid_quantity_and_precision_conflict_are_quarantined(self):
        rows = [self.row(raw_amount='1e6'), self.row(tx_hash='c1'), self.row(tx_hash='c2', decimals='18')]
        summary, _, issues = self.audit(rows)
        self.assertEqual(summary['groups'], [])
        self.assertEqual(len(issues), 3)

    def test_precision_conflict_in_duplicate_group_quarantines_other_asset_events(self):
        rows = [self.row(), self.row(decimals='18'), self.row(tx_hash='another')]
        summary, _, issues = self.audit(rows)
        self.assertEqual(summary['groups'], [])
        self.assertEqual(summary['decisions'], {'conflict': 2, 'precision_conflict': 1})
        self.assertEqual(len(issues), 3)

    def test_cli_cannot_overwrite_input_via_output_temporary_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            original = (SITE/'public/practice/crypto-forensics/movements.csv').read_bytes()
            for name in ['summary.json.tmp', 'decisions.csv.tmp', 'issues.csv.tmp']:
                with self.subTest(name=name):
                    source = folder/name
                    source.write_bytes(original)
                    failed = subprocess.run([sys.executable, str(SCRIPT), str(source), '--target', 'TARGET', '--out', str(folder)], capture_output=True)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertEqual(source.read_bytes(), original)

    def test_cli_replaces_prior_results_when_target_has_no_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'result'
            sample = SITE/'public/practice/crypto-forensics/movements.csv'
            command = [sys.executable, str(SCRIPT), str(sample), '--target', 'TARGET', '--out', str(output)]
            subprocess.run(command, check=True, capture_output=True)
            self.assertTrue(json.loads((output/'summary.json').read_text())['groups'])
            command[command.index('TARGET')] = 'MISSING'
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(json.loads((output/'summary.json').read_text())['groups'], [])
            with (output/'decisions.csv').open(newline='') as handle:
                self.assertFalse(any(row['decision'] in {'incoming', 'outgoing', 'fee'} for row in csv.DictReader(handle)))

    def test_published_fixture_matches_documented_scope_and_review_issues(self):
        sample = SITE/'public/practice/crypto-forensics/movements.csv'
        summary, _, issues = ledger.analyze(sample, 'TARGET', '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z')
        groups = {(g['chain'], g['asset_id']): g for g in summary['groups']}
        token = groups[('demo-evm-1', 'token:K')]
        self.assertEqual((token['incoming'], token['outgoing'], token['net_flow']), ('30.000000', '4.000000', '26.000000'))
        self.assertEqual((token['incoming_events'], token['positive_incoming_events']), (3, 2))
        self.assertEqual(groups[('demo-evm-1', 'native:ETH')]['fee'], '0.001600000000000000')
        self.assertEqual((summary['input_rows'], len(issues)), (22, 5))
        self.assertEqual(summary['decisions']['conflict'], 4)

    def test_bitcoin_article_script_handles_known_fee_and_missing_prevout(self):
        import re
        body = (SITE/'src/content-curation/forensic-crypto-bitcoin.md').read_text(encoding='utf-8')
        script = re.findall(r'```python\n(.*?)\n```', body, re.S)[0]
        fixture = json.loads((SITE/'public/practice/crypto-forensics/bitcoin-transaction.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            task_script, task_input = Path(directory)/'check.py', Path(directory)/'tx.json'
            task_script.write_text(script, encoding='utf-8')
            task_input.write_text(json.dumps(fixture), encoding='utf-8')
            command = [sys.executable, str(task_script), str(task_input)]
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
            numbers = json.loads(result.stdout)
            self.assertEqual((numbers['inputs_sat'], numbers['outputs_sat'], numbers['fee_sat']), (200000, 199000, 1000))
            self.assertEqual(numbers['fee_sat_per_vb'], '5')
            del fixture['vin'][0]['prevout']
            task_input.write_text(json.dumps(fixture), encoding='utf-8')
            failed = subprocess.run(command, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)

    def test_erc20_article_decoder_preserves_zero_and_rejects_conflicting_logs(self):
        import re
        body = (SITE/'src/content-curation/forensic-crypto-account-chains.md').read_text(encoding='utf-8')
        script = re.findall(r'```python\n(.*?)\n```', body, re.S)[0]
        token = '0x' + 'aa'*20
        transaction, block = '0x' + '11'*32, '0x' + '22'*32
        topic = '0x' + '00'*12 + '33'*20
        event = {'address': token, 'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', topic, topic],
                 'data': '0x' + format(25000000, '064x'), 'blockHash': block,
                 'transactionHash': transaction, 'logIndex': '0x0'}
        zero = {**event, 'logIndex': '0x1', 'data': '0x' + '00'*32}
        receipt = {'status': '0x1', 'transactionHash': transaction, 'blockHash': block,
                   'gasUsed': hex(50000), 'effectiveGasPrice': hex(20000000000), 'logs': [event, zero, event]}
        with tempfile.TemporaryDirectory() as directory:
            task_script, task_input = Path(directory)/'decode.py', Path(directory)/'receipt.json'
            task_script.write_text(script, encoding='utf-8')
            command = [sys.executable, str(task_script), str(task_input), token, '6']
            def invoke(value):
                task_input.write_text(json.dumps(value), encoding='utf-8')
                return subprocess.run(command, capture_output=True)
            decoded = invoke(receipt)
            self.assertEqual(decoded.returncode, 0, decoded.stderr)
            result = json.loads(decoded.stdout)
            self.assertEqual([r['amount_raw'] for r in result['events']], ['25000000', '0'])
            self.assertEqual(result['execution_fee_wei'], '1000000000000000')
            failed = invoke({**receipt, 'status': '0x0', 'logs': []})
            self.assertEqual(json.loads(failed.stdout)['events'], [])
            self.assertEqual(json.loads(failed.stdout)['execution_fee_wei'], '1000000000000000')
            conflict = {**event, 'data': '0x' + format(5000000, '064x')}
            self.assertNotEqual(invoke({**receipt, 'logs': [event, conflict]}).returncode, 0)
            wrong_block = {**event, 'blockHash': '0x' + '44'*32}
            self.assertNotEqual(invoke({**receipt, 'logs': [wrong_block]}).returncode, 0)


if __name__ == '__main__':
    unittest.main()
