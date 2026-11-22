#!/usr/bin/env python3
"""Synchronize the homepage fallback using the same renderer as the live hub."""
from __future__ import annotations

import argparse
import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class ContentRanges(HTMLParser):
    """Locate element contents without reserializing unrelated homepage HTML."""

    def __init__(self, source, ids):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.ids = ids
        self.stack = []
        self.ranges = {}
        self.lines = [0]
        self.lines.extend(i + 1 for i, char in enumerate(source) if char == '\n')
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            return
        element_id = dict(attrs).get('id')
        self.stack.append((tag, element_id, self.position() + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError(f'Unbalanced HTML near {tag}')
        _, element_id, start = self.stack.pop()
        if element_id in self.ids:
            self.ranges[element_id] = (start, self.position())


def render_homepage():
    # Running the existing renderer avoids a second set of taxonomy, ordering,
    # series-deduplication and date-format rules in this publishing tool.
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = {};
const document = {
  body: {getAttribute: () => 'home'},
  getElementById: id => nodes[id] || (nodes[id] = {}),
  querySelectorAll: () => []
};
const registry = JSON.parse(fs.readFileSync('registry.json', 'utf8'));
const context = {document, fetch: async () => ({ok: true, json: async () => registry})};
vm.runInNewContext(fs.readFileSync('assets/kerwin-hub.js', 'utf8'), context);
setImmediate(() => process.stdout.write(JSON.stringify(nodes)));
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if committed homepage content is stale')
    args = parser.parse_args()
    path = ROOT / 'index.html'
    source = path.read_text(encoding='utf-8')
    nodes = render_homepage()
    required = {'hub-date', 'library-count', 'library-count-secondary', 'ticker-items',
                'latest-lead', 'latest-list', 'earnings-list', 'axis-list', 'library-entry'}
    ranges = ContentRanges(source, required).ranges
    if required != ranges.keys():
        raise ValueError(f'Missing homepage elements: {required - ranges.keys()}')
    replacements = []
    for element_id in required:
        node = nodes[element_id]
        content = node.get('innerHTML')
        if content is None:
            content = escape(str(node['textContent']))
        start, end = ranges[element_id]
        replacements.append((start, end, content))
    updated = source
    for start, end, content in sorted(replacements, reverse=True):
        updated = updated[:start] + content + updated[end:]
    if args.check:
        if updated != source:
            print('Homepage fallback is stale. Run python3 tools/sync_homepage_fallback.py and commit index.html.')
            return 1
        print('Homepage fallback matches the approved registry and live renderer.')
    else:
        path.write_text(updated, encoding='utf-8')
        print('Synchronized homepage fallback from the approved registry.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
