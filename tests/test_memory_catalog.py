"""Guard the independent memory route and the complete pinned CLI catalog."""
from pathlib import Path
import json
import re
import unittest

SITE = Path(__file__).resolve().parents[1]


class MemoryCatalogTests(unittest.TestCase):
    def test_memory_pages_have_a_single_durable_home(self):
        registry = json.loads((SITE / 'src/data/forensics-supplements.json').read_text('utf-8'))
        articles = {a['id']: a for a in registry['articles']}
        memory = {key: value for key, value in articles.items() if value.get('track') == '内存取证'}
        self.assertEqual(len(memory), 6)
        self.assertEqual(len({p['topic'] for p in memory.values()}), 6)
        for identifier, data in memory.items():
            self.assertTrue((SITE / f'src/content-curation/{identifier}.md').is_file())
            published = (SITE / f'src/content/knowledge/{identifier}.md').read_text('utf-8')
            header = published.split('---', 2)[1]
            self.assertRegex(header, r'(?m)^track: ["\']?内存取证["\']?$')
            self.assertIn(data['topic'], header)
        self.assertEqual(articles['fic-case-07']['track'], '计算机取证')
        self.assertEqual(articles['fic-case-07']['topic'], '程序与恶意代码')
        for name in ('forensic-memory', 'forensic-memory-unix'):
            self.assertIn(name, memory, 'Keep historical article IDs')

    def test_complete_cli_names_options_and_aliases_are_visible(self):
        data = json.loads((SITE / 'src/data/volatility-catalog.json').read_text('utf-8'))
        body = (SITE / 'src/content-curation/forensic-memory-volatility.md').read_text('utf-8')
        for version in (2, 3):
            catalog = data[f'volatility{version}']
            names = [p['name'] for p in catalog['plugins']]
            self.assertEqual(len(names), len(set(names)), f'Vol{version} duplicate CLI keys')
            globals_ = catalog.get('globalOptions', catalog.get('global_options'))
            self.assertEqual(len(globals_), 23)
            for option in globals_:
                for flag in option.get('options', [option.get('long_option')]):
                    self.assertIn(f'`{flag}`', body)
            for plugin in catalog['plugins']:
                self.assertIn(f'`{plugin["name"]}`', body)
                parameters = plugin.get('parameters', plugin.get('options'))
                flags = [p.get('cliOption', p.get('long_option')) for p in parameters]
                self.assertEqual(len(flags), len(set(flags)), plugin['name'])
                for flag in flags:
                    self.assertIn(f'`{flag}`', body, plugin['name'])
                if plugin.get('deprecatedAlias'):
                    target = plugin['effectiveClass']
                    self.assertIn(target, names, plugin['name'])
                    canonical = next(p for p in catalog['plugins'] if p['name'] == target)
                    self.assertEqual([p['name'] for p in parameters], [p['name'] for p in canonical['parameters']], plugin['name'])
        old, new = data['volatility2'], data['volatility3']
        self.assertEqual(old['parse_errors'], [])
        self.assertEqual(old['unresolved_constructor_calls'], [])
        self.assertEqual(old['duplicate_cli_keys'], {})
        self.assertEqual(new['coverage']['missingFromStatic'], [])
        self.assertEqual(new['coverage']['runtimeRequirementDifferences'], [])
        self.assertEqual(new['coverage']['unresolvedStaticExpressions'], [])
        self.assertEqual(len(new['plugins']), new['coverage']['staticPluginCount'])
        self.assertEqual(len(old['plugins']), old['counts']['plugins'])


if __name__ == '__main__':
    unittest.main()
