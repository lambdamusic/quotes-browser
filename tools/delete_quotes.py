#!/usr/bin/env python
"""
Delete quotes from quote files.

    delete_quotes.py DELETE.json QUOTES_DIR

DELETE.json is a list of {"id": "<file slug>|<quote index>", "title": ...}.
In a multi-quote file the quote's block goes, from its heading to the next
heading; the title on that heading must match. When every quote in a file is
deleted (or it is a single-quote file), the file goes.
"""

import json
import os
import sys
from collections import defaultdict

from apply_titles import quote_headings


def delete(delete_path, quotes_dir):
    by_file = defaultdict(list)
    for d in json.load(open(delete_path)):
        slug, index = d['id'].split('|')
        by_file[slug].append((int(index), d['title']))

    removed_quotes, removed_files = 0, 0
    for slug, items in sorted(by_file.items()):
        path = os.path.join(quotes_dir, slug + '.md')
        lines = open(path, encoding='utf-8').read().split('\n')
        single = any(l.startswith('title: ') for l in lines[:lines.index('---', 1)])
        headings = [] if single else quote_headings(lines)
        if single or len(items) == len(headings):
            os.remove(path)
            removed_quotes += len(items)
            removed_files += 1
            continue
        # every heading line (quotes and chapters), to find where a block ends
        all_headings = [i for i, l in enumerate(lines) if l.strip().startswith(('# ', '## '))]
        spans = []
        for index, title in items:
            start = headings[index - 1]
            found = lines[start].strip().lstrip('#').strip()
            if found != title:
                raise SystemExit(f'{slug}|{index}: expected {title!r}, found {found!r}')
            end = next((h for h in all_headings if h > start), len(lines))
            spans.append((start, end))
        for start, end in sorted(spans, reverse=True):
            del lines[start:end]
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
        removed_quotes += len(items)
    print(f'{removed_quotes} quotes deleted, {removed_files} files removed')


if __name__ == '__main__':
    delete(*sys.argv[1:])
