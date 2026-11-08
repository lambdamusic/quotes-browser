#!/usr/bin/env python
"""
Convert a Kindle highlights export (kindle-sync markdown, in
004-library/kindle/) to the quotes multi-quote format:

    kindle_import.py extract BOOK.md OUT.json
        the highlights as JSON: n, location, text, and `dup` when the text is
        already in the quotes folder; title and tags are left empty

    (fill in "title" and "tags" for every highlight that isn't a dup)

    kindle_import.py write BOOK.md IN.json OUT_DIR
        writes YYYY-MM-DD-slug.md (the book's last-highlight date) into
        OUT_DIR, skipping duplicates

    kindle_import.py append IN.json QUOTES_FILE
        for a book already in quotes/: adds the new quotes at the end of its
        file, so it keeps one source page and the existing quote numbers

Write to a copy of the quotes folder first, and compare the parse before and
after (parser.read_all_files_data) before touching the real one.

All 22 books in kindle/ were imported this way on 2026-11-08 (see the README in
004-library/), with titles and tags written by Claude and reviewed. Run it
again only for new books or new highlights: `extract` flags what's already in.
The style the titles and tags followed: tags reuse existing ones, American
spelling for new ones; titles in sentence case, in the quote's language.
"""

import glob
import json
import os
import re
import sys

QUOTES_DIR = '/Users/michele.pasin/Dropbox/Apps/NVALT/004-library/quotes/'


def read_book(path):
    raw = open(path, encoding='utf-8').read()
    head, body = raw.split('## Highlights', 1)

    def field(name):
        # `title: >-` folds the value over the following indented lines
        m = re.search(r'^  %s: (?:>-\n((?:    .*\n)+)|(.*)$)' % name, head, re.M)
        if not m:
            return ''
        value = ' '.join(l.strip() for l in m.group(1).splitlines()) if m.group(1) else m.group(2)
        value = value.strip()
        if value[:1] == "'":
            value = value.strip("'").replace("''", "'")  # YAML single-quoted
        return value.strip('"')

    meta = {k: field(k) for k in ('title', 'author', 'asin', 'lastAnnotatedDate')}
    highlights = []
    for n, chunk in enumerate([c.strip() for c in body.split('\n---\n') if c.strip()], 1):
        m = re.search(r'\s*— location: \[(\d+)\]\(.*$', chunk, re.S)
        text = chunk[:m.start()] if m else chunk
        highlights.append({'n': n, 'location': int(m.group(1)) if m else None, 'text': text.strip()})
    return meta, highlights


def short_title(title):
    """'Mind: A Brief Introduction (Fundamentals of Philosophy) (...)' -> 'Mind: A Brief Introduction';
    a long subtitle goes ('The Lean Startup: The Million Copy Bestseller...' -> 'The Lean Startup')"""
    title = re.sub(r'\s*\([^)]*\)', '', title).strip()
    if len(title) > 40 and ':' in title:
        title = title.split(':', 1)[0].strip()
    return title


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text.lower().replace('’', '').replace("'", ''))
    return re.sub(r'[\s_-]+', '-', text).strip('-')


def _key(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()


def extract(book, out):
    meta, highlights = read_book(book)
    existing = _key(' '.join(open(f, encoding='utf-8').read() for f in glob.glob(QUOTES_DIR + '*.md')))
    for h in highlights:
        key = _key(h['text'])[:80]
        h['dup'] = len(key) > 40 and key in existing
        h['title'], h['tags'] = '', []
    json.dump({'meta': meta, 'highlights': highlights}, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f"{len(highlights)} highlights, {sum(h['dup'] for h in highlights)} already in quotes -> {out}")


def write(book, data_path, out_dir):
    meta, _ = read_book(book)
    data = json.load(open(data_path))
    source = f"{short_title(meta['title'])} ({meta['author']})"
    date = meta['lastAnnotatedDate']
    name = f"{date}-{slugify(short_title(meta['title']))}.md"
    lines = ['---', 'template: quote-multi.html', f'source: "{source}"',
             f"url: https://www.amazon.com/dp/{meta['asin']}", f'date: {date}', 'review: False', '---', '']
    blocks = quote_blocks(data['highlights'])
    lines += blocks
    kept = len(blocks) // 6
    path = os.path.join(out_dir, name)
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'{kept} quotes -> {path}')


def quote_blocks(highlights):
    lines = []
    for h in highlights:
        if h['dup']:
            continue
        assert h['title'] and h['tags'], f"highlight {h['n']} has no title or tags"
        lines += [f"# {h['title']}", ' '.join('#' + t for t in h['tags']), '', h['text'], '', '']
    return lines


def append(data_path, quotes_file):
    """add the new quotes at the end of an existing source file, for books
    already on the site, so the book keeps one source page and the existing
    quotes keep their numbers"""
    data = json.load(open(data_path))
    lines = quote_blocks(data['highlights'])
    text = open(quotes_file, encoding='utf-8').read().rstrip('\n')
    open(quotes_file, 'w', encoding='utf-8').write(text + '\n\n' + '\n'.join(lines))
    print(f'{len(lines) // 6} quotes appended -> {quotes_file}')


if __name__ == '__main__':
    cmd, *args = sys.argv[1:]
    {'extract': extract, 'write': write, 'append': append}[cmd](*args)
