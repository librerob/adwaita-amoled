#!/usr/bin/env python3
"""Read-only upstream tag watch. Reports review candidates, never compatibility."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def version(tag, prefixes):
    for prefix in prefixes:
        if tag.startswith(prefix):
            text = tag[len(prefix):]
            if re.fullmatch(r'\d+\.\d+(?:\.\d+)?', text):
                return tuple(map(int, text.split('.'))) + (0,) * (3 - len(text.split('.')))
    return None


def eligible(number, component):
    return (number is not None and number[0] >= component['min_major']
            and (component.get('max_major') is None or number[0] <= component['max_major'])
            and number[1] < 90
            and (not component['even_minor'] or number[1] % 2 == 0))


def load_config(path):
    config = json.loads(path.read_text())
    if config.get('version') != 1 or not isinstance(config.get('components'), list) or not config['components']:
        raise ValueError('Expected nonempty version 1 component catalog')
    seen = set()
    for c in config['components']:
        if not re.fullmatch(r'[a-z0-9-]+', c['id']) or c['id'] in seen:
            raise ValueError('Invalid or duplicate component identity')
        seen.add(c['id'])
        if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+', c['repo'])
                or c['repo'].split('/')[-1] in ('.', '..')):
            raise ValueError('Invalid repository')
        if not c['prefixes'] or not all(isinstance(p, str) for p in c['prefixes']):
            raise ValueError('Expected explicit tag prefixes')
        baseline = version(c['baseline_tag'], c['prefixes'])
        if not isinstance(c['even_minor'], bool) or not eligible(baseline, c):
            raise ValueError('Baseline does not match component stable-tag rules')
        if 'baseline_commit' in c and not re.fullmatch(r'[0-9a-f]{40}', c['baseline_commit']):
            raise ValueError('Invalid baseline commit')
    return config


def api_tags(repo, page):
    result = subprocess.run(['gh', 'api', f'repos/{repo}/tags?per_page=100&page={page}'],
                            capture_output=True, text=True, timeout=45)
    if result.returncode:
        # Do not echo credential/tool diagnostics into public reports.
        raise RuntimeError(f'GitHub tag request failed for {repo}, page {page}; check API access/rate limits')
    data = json.loads(result.stdout)
    if not isinstance(data, list) or any(not isinstance(t, dict) or not isinstance(t.get('name'), str)
                                       or not isinstance(t.get('commit', {}).get('sha'), str) for t in data):
        raise ValueError('Unexpected GitHub tags response')
    return data


def all_tags(repo, fetch=api_tags, max_pages=50):
    tags = []
    for page in range(1, max_pages + 1):
        batch = fetch(repo, page)
        tags.extend(batch)
        if len(batch) < 100:
            return tags
    raise RuntimeError(f'Tag pagination limit reached for {repo}; report is incomplete')


def inspect_component(component, tags):
    c = component
    baseline = version(c['baseline_tag'], c['prefixes'])
    by_name = {t['name']: t for t in tags}
    if c['baseline_tag'] not in by_name:
        raise ValueError('Baseline tag is absent upstream; review catalog/mirror before concluding anything')
    candidates = [(version(t['name'], c['prefixes']), t['name'], t['commit']['sha']) for t in tags]
    candidates = [t for t in candidates if eligible(t[0], c)]
    if not candidates:
        raise ValueError('No matching stable-looking numeric tags found')
    latest, tag, commit = max(candidates)
    moved = bool(c.get('baseline_commit') and by_name[c['baseline_tag']]['commit']['sha'] != c['baseline_commit'])
    comparison_base = c['baseline_commit'] if moved else c['baseline_tag']
    return {'id': c['id'], 'name': c['name'], 'repo': c['repo'], 'baseline': c['baseline_tag'],
            'latest': tag, 'latest_commit': commit,
            'status': 'review-needed' if latest > baseline or moved else 'no-new-tag',
            'baseline_commit_changed': moved, 'focus': c['focus'], 'tests': c['tests'],
            'source_url': f"https://github.com/{c['repo']}/tree/{quote(tag, safe='')}/{c['path']}",
            'compare_url': f"https://github.com/{c['repo']}/compare/{quote(comparison_base, safe='')}...{quote(tag, safe='')}"}


def collect(config, fetch=api_tags):
    cache = {}
    rows = []
    for c in config['components']:
        try:
            if c['repo'] not in cache:
                try:
                    cache[c['repo']] = all_tags(c['repo'], fetch)
                except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
                    cache[c['repo']] = error
            if isinstance(cache[c['repo']], Exception):
                raise cache[c['repo']]
            rows.append(inspect_component(c, cache[c['repo']]))
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
            rows.append({'id': c['id'], 'name': c['name'], 'repo': c['repo'],
                         'baseline': c['baseline_tag'], 'status': 'error', 'error': str(error)})
    return {'checked_at': datetime.now(timezone.utc).isoformat(), 'components': rows,
            'review_needed': sum(r['status'] == 'review-needed' for r in rows),
            'errors': sum(r['status'] == 'error' for r in rows)}


def markdown(report):
    lines = ['# Upstream review watch', '', f"Checked: {report['checked_at']}", '',
             '**New tags are review candidates, not confirmed bugs or compatibility results.**', '',
             '| Component | Review baseline | Latest matching tag | Result |',
             '| --- | --- | --- | --- |']
    for r in report['components']:
        latest = f"[{r['latest']}]({r['source_url']})" if r['status'] != 'error' else 'Unavailable'
        lines.append(f"| {r['name']} | `{r['baseline']}` | {latest} | {r['status']} |")
    for r in report['components']:
        if r['status'] == 'error':
            lines += ['', f"## {r['name']}: incomplete check", '', r['error']]
        elif r['status'] == 'review-needed':
            lines += ['', f"## {r['name']}: review needed", '', f"[Upstream changes]({r['compare_url']}) · [Source]({r['source_url']})", '',
                      r['focus'], '', 'Suggested validation: ' + r['tests']]
            if r['baseline_commit_changed']:
                lines += ['', '**The pinned baseline tag now points to a different commit. Investigate before importing it.**']
    lines += ['', '## Next steps', '',
              'Review upstream NEWS and relevant style/widget changes. Reproduce any suspected regression,',
              'fix confirmed problems, then run the affected native tests. Update the catalog baseline only',
              'after recording what was reviewed/tested in COMPATIBILITY.md; keep unsupported versions explicit.', '',
              'No-new-tag means this tag check found no newer matching release candidate. It does not prove',
              'bug-free operation or detect unreleased branch changes. GitHub mirrors may lag primary upstreams.',
              'Development suffixes, odd development minors where configured, and minor versions ≥90 are excluded.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'maintenance/upstream-watch.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'upstream-report')
    args = parser.parse_args()
    config = load_config(args.config)
    report = collect(config)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    content = markdown(report)
    (args.output / 'report.md').write_text(content)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write(content)
    print(f"Upstream watch: {report['review_needed']} review candidates; {report['errors']} incomplete checks.")
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for row in report['components']:
            if row['status'] == 'review-needed':
                print(f"::warning title=Upstream review needed::{row['id']}: {row['baseline']} -> {row['latest']}; see run summary")
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
