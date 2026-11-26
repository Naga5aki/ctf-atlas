import hashlib
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IOSUsageSupplementTests(unittest.TestCase):
    def read(self, ident):
        return (ROOT / f'src/content-curation/{ident}.md').read_text('utf-8')

    def test_directory_identity_and_state_limits(self):
        core = self.read('forensic-ios-forensics')
        for token in ('3.1 先辨别目录层级与别名', 'MCMMetadataIdentifier',
                      'compatibilityInfo', '不是文件系统材料中通用的容器 UUID 索引',
                      'rootless', 'known_hosts', '认证前', 'HISTFILE', 'bug_type'):
            self.assertIn(token, core)
        self.assertEqual(core.count('tqandjdc.github.io/2026/05/29/'), 1)
        self.assertNotIn('/Containers/Manifest.db', core)

    def test_path_matrix_is_conditional_and_corrected(self):
        core = self.read('forensic-ios-forensics')
        for token in ('CallHistory.storedata', 'CallHistoryTemp.storedata', 'Bookmarks.db',
                      'NoteStore.sqlite', 'PhotoData/Photos.sqlite', 'AddressBookImages.sqlitedb',
                      'Calendar.sqlitedb', 'com.apple.wifi.known-networks.plist',
                      'JoinedBySystemAt', '以实际命中路径为准', 'ZGENERICASSET / ZASSET'):
            self.assertIn(token, core)
        for incorrect in ('imessage.db', 'callhistory.db', 'PhotoData.sqlite', 'keydb.sqlitedb'):
            self.assertNotIn(incorrect, core)

    def test_published_sms_join_keeps_missing_handles_and_deduplicates(self):
        body = self.read('forensic-ios-backup')
        match = re.search(r'```sql\n(SELECT m\.ROWID AS message_rowid,.*?);\n```', body, re.S)
        self.assertIsNotNone(match)
        self.assertIn('COUNT(DISTINCT m.ROWID)', body)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sms.db'
            c = sqlite3.connect(path)
            c.executescript('''
                CREATE TABLE handle(id TEXT);
                CREATE TABLE message(handle_id INTEGER, service TEXT, is_from_me INTEGER,
                                     date INTEGER, is_read INTEGER, text TEXT);
                CREATE TABLE message_attachment_join(message_id INTEGER, attachment_id INTEGER);
                INSERT INTO handle VALUES ('sample-account');
                INSERT INTO message VALUES (1,'iMessage',1,1000000000,1,'sample text');
                INSERT INTO message VALUES (99,'SMS',0,2000000000,0,NULL);
                INSERT INTO message_attachment_join VALUES (1,10),(1,11),(2,12);
            ''')
            c.close()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            c = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
            rows = c.execute(match.group(1)).fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], 'sample-account')
            self.assertIsNone(rows[1][1])
            counts = c.execute('''SELECT COUNT(*), COUNT(DISTINCT m.ROWID)
                FROM message m LEFT JOIN message_attachment_join a ON m.ROWID=a.message_id''').fetchone()
            self.assertEqual(counts, (3, 2))
            with self.assertRaises(sqlite3.OperationalError):
                c.execute('DELETE FROM message')
            c.close()
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_offline_workflow_separates_recovery_from_evidence(self):
        tools = self.read('forensic-ios-tools')
        for token in ("find -P ./work/extracted", '候选路径清单，不是业务记录', 'lost_and_found',
                      '--ignore-freelist', '未执行损坏库', '回查 SQL',
                      'recovery-run-01/recovered.sqlite', '## 10 故障排查',
                      'mkdir ./output/recovery-run-01 || exit 1', 'sqlite3 -bail'):
            self.assertIn(token, tools)
        self.assertNotIn('find -L', tools)
        self.assertNotIn('VACUUM;', tools)


if __name__ == '__main__':
    unittest.main()
