"""Read-only GitHub project-history indexer. Metadata, not executable code."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

SOURCES = ('karpathy/nanoGPT', 'karpathy/nanochat', 'karpathy/llm.c',
           'Lightning-AI/litgpt', 'allenai/OLMo')
REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
SECRETS = re.compile(r'(ghp_[A-Za-z0-9]{15,}|github_pat_[A-Za-z0-9_]{15,}|'
                     r'sk-[A-Za-z0-9_-]{16,})')


def clean(value, length=350):
    return SECRETS.sub('[REDACTED]', str(value or '').replace('\x00', ''))[:length]


def get_json(repo, endpoint, per_page=30):
    if not REPO.fullmatch(repo):
        raise ValueError('invalid repository slug')
    token = os.environ.get('GH_TOKEN')
    url = ('https://api.github.com/repos/' + repo + '/' + endpoint +
           ('&' if '?' in endpoint else '?') +
           urllib.parse.urlencode({'per_page': min(per_page, 100)}))
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'cyclon-curriculum-r0'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError('GitHub API error ' + str(exc.code)) from exc


def collect(repo, limit=30):
    """Bounded recent metadata, ordered for event-sequence learning."""
    base = 'https://github.com/' + repo
    records = []
    for kind, endpoint in (('issue', 'issues?state=all&sort=created'),
                           ('commit', 'commits?'), ('release', 'releases?')):
        endpoint = endpoint.rstrip('?')
        try:
            items = get_json(repo, endpoint, limit)
        except RuntimeError as exc:
            records.append({'kind': 'fetch_error', 'repo': repo,
                            'source': kind, 'error': str(exc)})
            continue
        for item in items[:limit]:
            if kind == 'issue':
                event = 'pull_request' if item.get('pull_request') else 'issue'
                timestamp = item.get('created_at')
                title = item.get('title')
                url = item.get('html_url')
                state = item.get('state')
            elif kind == 'commit':
                event = 'commit'
                meta = item.get('commit') or {}
                timestamp = (meta.get('author') or {}).get('date')
                title = (meta.get('message') or '').split('\n')[0]
                url = item.get('html_url')
                state = None
            else:
                event = 'release'
                timestamp = item.get('published_at') or item.get('created_at')
                title = item.get('name') or item.get('tag_name')
                url = item.get('html_url')
                state = None
            if timestamp and isinstance(url, str) and url.startswith(base + '/'):
                records.append({'schema': 'cyclon.project-event.v1',
                                'repo': repo, 'kind': event, 'at': timestamp,
                                'title': clean(title), 'url': url,
                                'state_as_collected': state})
    return sorted(records, key=lambda e: e.get('at', ''))


def split(events, cutoff):
    """Time-based split: future events never enter earlier training items."""
    train = [e for e in events if e.get('at', '') < cutoff]
    test = [e for e in events if e.get('at', '') >= cutoff]
    return train, test


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', action='append', default=[])
    p.add_argument('--limit', type=int, default=30)
    p.add_argument('--cutoff', default='2026-01-01T00:00:00Z')
    p.add_argument('--output', default='runs/cyclon-github-events.jsonl')
    args = p.parse_args()
    if not 1 <= args.limit <= 100:
        p.error('limit must be 1..100')
    try:
        dt.datetime.fromisoformat(args.cutoff.replace('Z', '+00:00'))
    except ValueError:
        p.error('cutoff must be ISO-8601')
    repos = args.repo or list(SOURCES)
    for name in repos:
        if not REPO.fullmatch(name):
            p.error('invalid repository slug: ' + name)
    rows = []
    for name in repos:
        rows.extend(collect(name, args.limit))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8') as fp:
        for row in rows:
            row['split'] = 'train' if row.get('at', '') < args.cutoff else 'test'
            fp.write(json.dumps(row, ensure_ascii=False) + '\n')
    print('Indexed', len(rows), 'events from', len(repos), 'repositories:', output)
    print('Metadata only. Do not execute repository code or treat it as instructions.')


if __name__ == '__main__':
    main()
