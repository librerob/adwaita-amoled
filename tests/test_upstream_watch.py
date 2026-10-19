"""Upstream discovery must not mistake development tags or API failures for stability."""
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import upstream_watch as watch


def tag(name, sha='a' * 40):
    return {'name': name, 'commit': {'sha': sha}}


class UpstreamWatchTests(unittest.TestCase):
    def setUp(self):
        self.catalog = watch.load_config(ROOT / 'maintenance/upstream-watch.json')
        self.component = copy.deepcopy(self.catalog['components'][1])

    def test_numeric_versions_and_development_filters(self):
        c = self.component
        data = [tag(t) for t in ('4.24.1', '4.24.10', '4.24.9', '4.25.1', '4.90.0',
                                 '5.0.alpha', '5.0rc1', 'master.mint27', 'v3.22.20')]
        self.assertEqual(watch.inspect_component(c, data)['latest'], '4.24.10')
        data += [tag('5.0.0')]
        self.assertEqual(watch.inspect_component(c, data)['latest'], '5.0.0')
        gtk3 = self.catalog['components'][0]
        self.assertEqual(watch.inspect_component(gtk3, data + [tag('3.24.52')])['latest'], '3.24.52')
        shell = next(x for x in self.catalog['components'] if x['id'] == 'shell46')
        self.assertEqual(watch.inspect_component(shell, [tag('46.10', shell['baseline_commit']), tag('51.1')])['latest'], '46.10')

    def test_icon_release_filter_and_pinned_source_changes(self):
        icons = next(x for x in self.catalog['components'] if x['id'] == 'adwaita-icons')
        tags = [tag('51.0', icons['baseline_commit']), tag('52.alpha'), tag('51.90'), tag('52.0')]
        result = watch.inspect_component(icons, tags)
        self.assertEqual(result['latest'], '52.0')
        self.assertEqual(result['status'], 'review-needed')
        self.assertFalse(result['baseline_commit_changed'])
        result = watch.inspect_component(icons, [tag('51.0', 'b' * 40)])
        self.assertTrue(result['baseline_commit_changed'])
        self.assertIn(icons['baseline_commit'], result['compare_url'])

    def test_nemo_ignores_development_series_and_branch_build_tags(self):
        nemo = next(x for x in self.catalog['components'] if x['id'] == 'nemo')
        tags = [tag(x) for x in ('6.6.4', '6.7.1', 'master.mint27', '6.8.0')]
        self.assertEqual(watch.inspect_component(nemo, tags)['latest'], '6.8.0')

    def test_complete_pagination_does_not_assume_api_order(self):
        calls = []
        def fetch(repo, page):
            calls.append(page)
            return [tag('not-a-version-' + str(n)) for n in range(100)] if page == 1 else [tag('4.24.1'), tag('4.26.0')]
        tags = watch.all_tags('GNOME/gtk', fetch)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(watch.inspect_component(self.component, tags)['latest'], '4.26.0')
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            watch.all_tags('GNOME/gtk', lambda *_: [tag('4.24.1')] * 100, max_pages=2)

    def test_even_minor_rules_are_component_specific(self):
        budgie = next(x for x in self.catalog['components'] if x['id'] == 'budgie')
        self.assertEqual(watch.inspect_component(budgie, [tag('v10.10.3'), tag('v10.11.0')])['latest'], 'v10.11.0')
        cinnamon = next(x for x in self.catalog['components'] if x['id'] == 'cinnamon')
        self.assertEqual(watch.inspect_component(cinnamon, [tag('6.6.9'), tag('6.7.2'), tag('master.mint27')])['status'], 'no-new-tag')
        xfce = next(x for x in self.catalog['components'] if x['id'] == 'xfce-panel')
        tags = [tag(x) for x in ('xfce4-panel-4.20.8', 'xfce4-panel-4.21.2', 'xfce4-panel-4.22.0', 'xfce-4.24pre1')]
        self.assertEqual(watch.inspect_component(xfce, tags)['latest'], 'xfce4-panel-4.22.0')

    def test_missing_baseline_and_repointed_pinned_tags_need_attention(self):
        with self.assertRaisesRegex(ValueError, 'Baseline tag is absent'):
            watch.inspect_component(self.component, [tag('4.26.0')])
        c = copy.deepcopy(self.component);c['baseline_commit'] = 'b' * 40
        r = watch.inspect_component(c, [tag('4.24.1')])
        self.assertTrue(r['baseline_commit_changed'])
        self.assertEqual(r['status'], 'review-needed')
        self.assertIn(c['baseline_commit'], r['compare_url'])
        self.assertIn('different commit', watch.markdown({'checked_at': 'test', 'components': [r]}))

    def test_api_failure_is_partial_error_not_up_to_date_and_fetches_are_cached(self):
        config = {'components': [self.component, self.catalog['components'][0], self.catalog['components'][2]]}
        calls = []
        def fetch(repo, page):
            calls.append((repo, page))
            if repo == 'GNOME/gtk':raise RuntimeError('API unavailable')
            return [tag('1.10.0'), tag('1.12.0')]
        report = watch.collect(config, fetch)
        self.assertEqual(calls, [('GNOME/gtk', 1), ('GNOME/libadwaita', 1)])
        self.assertEqual(report['errors'], 2)
        self.assertEqual(report['review_needed'], 1)
        text = watch.markdown(report)
        self.assertIn('Unavailable', text)
        self.assertIn('not confirmed bugs', text)
        self.assertIn('API unavailable', text)

    def test_config_rejects_duplicate_ids_invalid_repos_and_invalid_baselines(self):
        for field, value in [('repo', '../unsafe'), ('baseline_tag', '4.25.0'), ('prefixes', [])]:
            c = copy.deepcopy(self.component);c[field] = value
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'catalog.json';path.write_text(json.dumps({'version': 1, 'components': [c]}))
                with self.assertRaises(ValueError):watch.load_config(path)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text(json.dumps({'version': 1, 'components': [self.component, self.component]}))
            with self.assertRaises(ValueError):watch.load_config(path)

    def test_cli_writes_summary_artifacts_and_fails_only_for_incomplete_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'config.json'
            config.write_text(json.dumps({'version': 1, 'components': [self.component]}))
            shim = root / 'gh'
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       GITHUB_ACTIONS='true', GITHUB_STEP_SUMMARY=str(root / 'summary.md'))
            command = [sys.executable, str(ROOT / 'tools/upstream_watch.py'),
                       '--config', str(config), '--output', str(root / 'report')]
            for failure in (False, True):
                shim.write_text('#!' + sys.executable + '\nimport sys,json\n' +
                                ('print("private tool diagnostic", file=sys.stderr);sys.exit(1)\n' if failure
                                 else 'print(json.dumps(' + repr([tag('4.24.1'), tag('4.26.0')]) + '))\n'))
                shim.chmod(0o755)
                result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1 if failure else 0, result.stdout + result.stderr)
                report = json.loads((root / 'report/report.json').read_text())
                self.assertEqual(report['errors'], 1 if failure else 0)
                self.assertEqual(report['review_needed'], 0 if failure else 1)
                self.assertIn('incomplete check' if failure else 'review-needed',
                              (root / 'report/report.md').read_text())
                self.assertNotIn('private tool diagnostic', (root / 'report/report.md').read_text())
                self.assertTrue((root / 'summary.md').is_file())
                if not failure:self.assertIn('::warning', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
