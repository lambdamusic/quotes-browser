#!/usr/bin/env python
"""
Write new titles into quote files.

    apply_titles.py TITLES.json QUOTES_DIR

TITLES.json is a list of {"id": "<file slug>|<quote index>", "old": ..., "title": ...}.
Single-quote files carry the title in the front matter (`title: "..."`).
Multi-quote files carry it as a `# ` or `## ` heading; the Nth quote is the
Nth heading with text under it, counted as parser._parse_markdown_multi does,
so files with the same title twice still get the right line. The old title
must match what is on that line, and only those lines change.
"""

import json
import sys
from collections import defaultdict


def quote_headings(lines):
    """line numbers of the headings that start a quote, in order"""
    body = lines.index('---', 1) + 1  # after the front matter
    out, current, has_text = [], None, False
    for i in range(body, len(lines)):
        l = lines[i].strip()
        if l.startswith('# ') or l.startswith('## '):
            if current is not None and has_text:
                out.append(current)
            current, has_text = i, False
        elif l.startswith('#'):
            continue  # tags
        elif l and current is not None:
            has_text = True
    if current is not None and has_text:
        out.append(current)
    return out


def apply(titles_path, quotes_dir):
    by_file = defaultdict(list)
    for t in json.load(open(titles_path)):
        slug, index = t['id'].split('|')
        by_file[slug].append((int(index), t['old'], t['title']))

    changed = 0
    for slug, items in sorted(by_file.items()):
        path = f'{quotes_dir.rstrip("/")}/{slug}.md'
        lines = open(path, encoding='utf-8').read().split('\n')
        single = any(l.startswith('title: ') for l in lines[:lines.index('---', 1)])
        headings = None if single else quote_headings(lines)
        for index, old, new in items:
            if single:
                i = next(i for i, l in enumerate(lines) if l.startswith('title: '))
                current = lines[i][len('title: '):].strip()[1:-1]
            else:
                i = headings[index - 1]
                current = lines[i].strip().lstrip('#').strip()
            if current != old:
                raise SystemExit(f'{slug}|{index}: expected title {old!r}, found {current!r}')
            lines[i] = f'title: "{new}"' if single else lines[i][:lines[i].index(' ') + 1] + new
            changed += 1
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'{changed} titles written in {len(by_file)} files')


if __name__ == '__main__':
    apply(*sys.argv[1:])
