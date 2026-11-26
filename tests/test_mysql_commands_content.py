import hashlib
import json
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
ID='forensic-database-recovery'

class MySQLCommandContentTests(unittest.TestCase):
    def body(self):return (ROOT/f'src/content-curation/{ID}.md').read_text('utf-8')

    def addition(self):return self.body().split('## 12 ',1)[1]

    def test_existing_body_and_other_topics_preserved(self):
        from test_baota_binding_content import reviewed_preservation_hash, reviewed_preservation_prefix
        rec=json.loads((ROOT/'docs/forensics-mysql-commands-preservation.json').read_text('utf-8'))
        old=rec['original_page'];now=(ROOT/old['path']).read_bytes()
        size, expected = reviewed_preservation_prefix(old['path'], old['bytes'], old['sha256'])
        self.assertEqual(hashlib.sha256(now[:size]).hexdigest(),expected)
        for n,h in rec['protected_files'].items():
            self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),reviewed_preservation_hash(n,h),n)

    def test_durable_existing_page_and_taxonomy(self):
        now=(ROOT/f'src/content/knowledge/{ID}.md').read_text('utf-8')
        self.assertEqual(self.body().strip(),now.split('---',2)[2].strip())
        self.assertIn('## 12 ',self.body())
        self.assertIn('track: 服务器取证',now.split('---',2)[1])
        self.assertIn('topic: Web 与数据库',now.split('---',2)[1])

    def test_common_cli_and_sql_commands_have_context(self):
        b=self.addition()
        for term in ['mysql --no-defaults','--protocol=TCP','--socket','--batch','--raw','--quick','--execute','mysqldump','mysqlbinlog','mysqladmin','SHOW DATABASES','SHOW FULL TABLES','SHOW CREATE TABLE','SHOW INDEX','INFORMATION_SCHEMA.COLUMNS','SHOW GRANTS','EXPLAIN','SHOW FULL PROCESSLIST','SHOW ENGINE INNODB STATUS','sql_mode','--no-login-paths']:
            self.assertIn(term,b,term)
        self.assertGreaterEqual(len(re.findall(r'^## ',b,re.M)),10)

    def test_aggregation_time_and_encoding_pitfalls(self):
        b=self.addition()
        for term in ['COUNT(DISTINCT','SUM(DISTINCT','HAVING','LEFT JOIN','COALESCE','NULLIF','DECIMAL','FROM_UNIXTIME','INET_NTOA','CHAR_LENGTH','HEX(','半开区间','ONLY_FULL_GROUP_BY','递归','ROW_NUMBER','JSON_EXTRACT','MySQL 5.7','MySQL 8']:
            self.assertIn(term,b,term)

    def test_recovery_logging_export_boundaries(self):
        b=self.addition()
        for term in ['ibd2sdi','innodb_force_recovery','DISCARD TABLESPACE','IMPORT TABLESPACE','myisamchk','--single-transaction','--no-tablespaces','DECODE-ROWS','事务边界','--stop-position','gtid','general_log','--initialize','--skip-grant-tables','OUTFILE','CSV','副本']:
            self.assertIn(term,b,term)

    def test_real_competition_mapping_and_synthetic_material(self):
        rec=json.loads((ROOT/'docs/forensics-mysql-commands-coverage.json').read_text('utf-8'))
        self.assertGreaterEqual(len(rec['contest_cases']),6)
        for item in rec['contest_cases']:
            self.assertTrue(item['url'].startswith('https://'))
            self.assertIn(item['target_heading'],self.body())
        self.assertGreaterEqual(len(rec['command_groups']),16)
        practice=ROOT/'public/practice/mysql-forensics'
        schema=(practice/'schema.sql').read_text('utf-8')
        queries=(practice/'queries.sql').read_text('utf-8')
        self.assertIn('forensic_lab',schema)
        self.assertNotRegex(queries,r'(?im)^\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b')
        self.assertIn('COUNT(DISTINCT',queries)
        self.assertIn('SUM(DISTINCT',queries)
        self.assertIn('自建',(practice/'README.md').read_text('utf-8'))
        self.assertTrue(json.loads((practice/'expected-results.json').read_text('utf-8')))
        self.assertNotRegex(self.addition(),r'第[一二三四五六七八九十0-9]+届|美亚杯|数证杯|蓝帽杯|题号')
        self.assertNotIn('源文件',self.addition())
        self.assertNotRegex(self.addition(),r'(?:服|计|网)[（(]?[0-9一二三四五六七八九十]+')

if __name__=='__main__':unittest.main()
