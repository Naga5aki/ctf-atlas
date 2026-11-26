"""Run article examples against controlled timestamps and synthetic SQLite records."""
import hashlib
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def blocks(name, language):
    text = (ROOT / 'src/content/knowledge' / f'{name}.md').read_text('utf-8')
    return re.findall(r'```' + re.escape(language) + r'\n(.*?)```', text, re.S)


def queries(name):
    statements = []
    for block in blocks(name, 'sql'):
        pending = ''
        for char in block:
            pending += char
            if char == ';' and sqlite3.complete_statement(pending):
                statements.append(pending.strip())
                pending = ''
        if pending.strip():
            statements.append(pending.strip())
    return statements


class ForensicsWebExamples(unittest.TestCase):
    def test_mp4_repair_changes_only_structural_offsets_and_keeps_input(self):
        script = blocks('fic-case-09', 'python')[0]
        def box(kind, payload):
            return struct.pack('>I4s', len(payload) + 8, kind) + payload

        def movie(offset):
            tables = box(b'stco', struct.pack('>III', 0, 1, offset))
            tables += box(b'co64', struct.pack('>IIQ', 0, 1, offset))
            content = box(b'stbl', tables)
            for kind in (b'minf', b'mdia', b'trak', b'moov'):
                content = box(kind, content)
            return content

        header = box(b'ftyp', b'isom' + struct.pack('>I', 0))
        payload = b'media bytes stco' + struct.pack('>III', 0, 1, 1)
        media_start = len(header) + len(movie(0)) + 8
        corrupted = header + movie(media_start - 7) + box(b'mdat', payload)
        corrected = header + movie(media_start) + box(b'mdat', payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program, original, output = root / 'repair.py', root / 'input.mp4', root / 'output.mp4'
            program.write_text(script, encoding='utf-8')
            original.write_bytes(corrupted)
            result = subprocess.run([sys.executable, '-X', 'utf8', str(program), str(original), str(output), '--delta', '7'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), corrected)
            self.assertEqual(original.read_bytes(), corrupted)
            self.assertIn('modified_entries= 2', result.stdout)
            for name, specimen, delta in (
                ('outside', corrupted, 100000),
                ('negative', corrupted, -100000),
                ('fragmented', corrupted + box(b'moof', b''), 7),
                ('truncated', corrupted[:-1], 7),
            ):
                original.write_bytes(specimen)
                rejected = root / f'{name}.mp4'
                result = subprocess.run([sys.executable, '-X', 'utf8', str(program), str(original), str(rejected), '--delta', str(delta)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, name)
                self.assertFalse(rejected.exists(), name)
                self.assertEqual(original.read_bytes(), specimen, name)

    def test_documented_timestamp_examples_and_subsecond_precision(self):
        scope = {}
        with redirect_stdout(StringIO()) as out:
            exec(blocks('forensic-time-evidence', 'python')[0], scope)
        self.assertEqual(out.getvalue().splitlines(), ['2024-01-01T00:00:00+00:00'] * 4)
        convert = scope['convert_timestamp']
        self.assertEqual(convert(-1, 'unix_ms'), '1969-12-31T23:59:59.999000+00:00')
        self.assertEqual(convert(1704067200123456789, 'unix_ns'), '2024-01-01T00:00:00.123456+00:00')

    def test_chromium_queries_preserve_visit_and_download_relationships(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.executescript('''
                CREATE TABLE urls(id INTEGER, url TEXT, title TEXT, visit_count INTEGER);
                CREATE TABLE visits(id INTEGER, url INTEGER, visit_time INTEGER, from_visit INTEGER, transition INTEGER);
                CREATE TABLE downloads(id INTEGER, target_path TEXT, tab_url TEXT, start_time INTEGER,
                    end_time INTEGER, received_bytes INTEGER, total_bytes INTEGER, state INTEGER);
                CREATE TABLE downloads_url_chains(id INTEGER, chain_index INTEGER, url TEXT);
                CREATE TABLE keyword_search_terms(url_id INTEGER, term TEXT);
                INSERT INTO urls VALUES(9,'https://example.test/search','synthetic',8);
                INSERT INTO visits VALUES(101,9,13348540800000000,0,1);
                INSERT INTO visits VALUES(102,9,13348540801000000,101,1);
                INSERT INTO downloads VALUES(5,'/tmp/a.bin','https://example.test/',13348540800000000,
                    13348540801000000,4,4,1);
                INSERT INTO downloads_url_chains VALUES(5,0,'https://example.test/redirect');
                INSERT INTO downloads_url_chains VALUES(5,1,'https://example.test/a.bin');
                INSERT INTO keyword_search_terms VALUES(9,'目标词');
            ''')
            sql = queries('forensic-browser')
            visits = db.execute(sql[0]).fetchall()
            self.assertEqual([r[0] for r in visits], [101, 102])
            self.assertEqual(visits[0][5], '2024-01-01 00:00:00')
            self.assertEqual(visits[1][6], 101)
            self.assertEqual(db.execute(sql[1]).fetchone()[0], 5)
            chains = db.execute(sql[2]).fetchall()
            self.assertEqual([(r[0], r[1]) for r in chains], [(5, 0), (5, 1)])
            self.assertEqual(db.execute(sql[3]).fetchone()[0], '目标词')

    def test_firefox_join_uses_place_id_and_keeps_bookmark_folders(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.executescript('''
                CREATE TABLE moz_places(id INTEGER, url TEXT, title TEXT);
                CREATE TABLE moz_historyvisits(id INTEGER, place_id INTEGER, visit_date INTEGER,
                    from_visit INTEGER, visit_type INTEGER);
                CREATE TABLE moz_bookmarks(id INTEGER, parent INTEGER, title TEXT, fk INTEGER, position INTEGER);
                INSERT INTO moz_places VALUES(44,'https://example.test/','home');
                INSERT INTO moz_historyvisits VALUES(900,44,1704067200000000,0,1);
                INSERT INTO moz_bookmarks VALUES(2,0,'folder',NULL,0);
                INSERT INTO moz_bookmarks VALUES(3,2,'link',44,0);
            ''')
            sql = queries('forensic-browser')
            row = db.execute(sql[4]).fetchone()
            self.assertEqual(row[0], 900)
            self.assertEqual(row[4], '2024-01-01 00:00:00')
            bookmarks = db.execute(sql[5]).fetchall()
            self.assertEqual(bookmarks[0][3], None)
            self.assertEqual(bookmarks[1][3], 'https://example.test/')

    def test_wal_snapshot_contains_committed_row_missing_from_main_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'app.db'
            with closing(sqlite3.connect(original)) as writer:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('PRAGMA wal_autocheckpoint=0')
                writer.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY, body TEXT)')
                writer.commit()
                writer.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                writer.execute("INSERT INTO messages VALUES(1,'committed-in-wal')")
                writer.commit()
                digest = hashlib.sha256(original.read_bytes()).hexdigest()
                missing_wal = root / 'main-only.db'
                shutil.copy2(original, missing_wal)
                with closing(sqlite3.connect(f'file:{missing_wal}?immutable=1', uri=True)) as main:
                    self.assertEqual(main.execute('SELECT count(*) FROM messages').fetchone()[0], 0)
                work = root / 'work'
                work.mkdir()
                for suffix in ('', '-wal', '-shm'):
                    shutil.copy2(root / f'app.db{suffix}', work / f'app.db{suffix}')
                with closing(sqlite3.connect(work / 'app.db')) as reader, closing(sqlite3.connect(work / 'snapshot.db')) as snapshot:
                    reader.backup(snapshot)
                    self.assertEqual(snapshot.execute('SELECT body FROM messages').fetchone()[0], 'committed-in-wal')
                    self.assertEqual(snapshot.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)

    def test_ios_manifest_path_hash_is_not_a_content_hash(self):
        scope = {}
        with redirect_stdout(StringIO()):
            exec(blocks('forensic-ios-backup', 'python')[0], scope)
        self.assertEqual(scope['file_id'], '3d0d7e5fb2ce288813306e4d4636395e047a3d28')
        self.assertEqual(scope['candidate'].parts[-2:], ('3d', scope['file_id']))
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE Files(domain TEXT, relativePath TEXT, fileID TEXT)')
            db.execute('INSERT INTO Files VALUES(?,?,?)', (scope['domain'], scope['relative'], scope['file_id']))
            db.execute("INSERT INTO Files VALUES('AppDomain-example','Library/other.db','unrelated')")
            rows = db.execute(blocks('forensic-ios-backup', 'sql')[0]).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][2], scope['file_id'])


if __name__ == '__main__':
    unittest.main()
