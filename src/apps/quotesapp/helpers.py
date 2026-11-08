#!/usr/bin/env python
# encoding: utf-8

"""
Data for the pages: quotes annotated for lists, latest and related quotes,
tag and source indexes. Everything here works on the list of quote dicts
from parser.read_all_files_data().

The site is mirrored to static HTML: anything picked at random is either
seeded by the data (featured) or picked in the browser (/random/), so a
site dump only rewrites pages whose quotes changed.
"""

import math
import random
import re
from collections import Counter, OrderedDict

import markdown
from django.utils.html import strip_tags


# ===========
# quote helpers
# ===========


def annotate(quote, excerpt_chars=280):
    """add the fields the templates need to a quote dict (in place)

    titled
        False when the title is just the opening words of the quote
        ('When designing a traditional architecture...'), so templates can
        show the text instead of repeating it
    plain / excerpt
        the quote as plain text, whole and shortened
    """
    title = quote['title'] or ''
    quote['titled'] = bool(title) and title != 'Untitled' and not title.endswith('...')
    if 'plain' not in quote:
        html = markdown.markdown(quote['markdown'] or '')
        quote['plain'] = re.sub(r'\s+', ' ', strip_tags(html)).strip()
    plain = quote['plain']
    if len(plain) > excerpt_chars:
        plain = plain[:excerpt_chars].rsplit(' ', 1)[0].rstrip(',;:.') + '…'
    quote['excerpt'] = plain
    return quote


def latest(files_data, n=10, per_source=2):
    """the most recently saved quotes, at most `per_source` from each source,
    so one long book import doesn't fill the list"""
    ordered = sorted(files_data, key=lambda q: (str(q['date']), q['quotesource'], -int(q['quoteindex'])), reverse=True)
    seen, out = Counter(), []
    for q in ordered:
        if not (q['markdown'] or '').strip():
            continue  # a bare '# Chapter' heading parsed as a quote
        if seen[q['quotesource']] < per_source:
            seen[q['quotesource']] += 1
            out.append(annotate(q))
        if len(out) == n:
            break
    return out


def featured(files_data, min_chars=160, max_chars=700):
    """a random quote short enough to set large, seeded by the number of
    quotes: it changes when quotes are added, not on every site dump"""
    pool = [q for q in files_data if min_chars <= len(q['markdown'] or '') <= max_chars]
    pool = sorted(pool or files_data, key=lambda q: (q['quotesource'], int(q['quoteindex'])))
    return annotate(dict(random.Random(len(files_data)).choice(pool)), excerpt_chars=max_chars + 100)


def related(quote, files_data, n=6):
    """quotes from other sources ranked by the tags they share, each tag
    weighted by its rarity (idf), so sharing #things counts for little"""
    tags = set(quote['tags'])
    df = tag_counts(files_data)
    total = len(files_data)
    scored = []
    for q in files_data:
        if q['quotesource'] == quote['quotesource']:
            continue
        shared = tags.intersection(q['tags'])
        if shared and (q['markdown'] or '').strip():
            score = sum(math.log(total / df[t]) for t in shared)
            scored.append((score, q, sorted(shared)))
    scored.sort(key=lambda x: (-x[0], x[1]['title']))
    out = []
    for score, q, shared in scored[:n]:
        q = annotate(dict(q), excerpt_chars=160)
        q['shared'] = shared
        out.append(q)
    return out


def siblings(quote, files_data):
    """the other quotes in the same source file, in file order, plus the
    previous and next one"""
    same = sorted([q for q in files_data if q['quotesource'] == quote['quotesource']],
                  key=lambda q: int(q['quoteindex']))
    idx = [int(q['quoteindex']) for q in same]
    here = idx.index(int(quote['quoteindex'])) if int(quote['quoteindex']) in idx else None
    prev = same[here - 1] if here else None
    nxt = same[here + 1] if here is not None and here + 1 < len(same) else None
    return same, prev, nxt


def tag_sizes(tags, files_data):
    counts = tag_counts(files_data)
    return sorted([(t, counts.get(t, 0)) for t in tags if t], key=lambda x: -x[1])


def quote_counts(files_data):
    """[[source slug, number of quotes], ...], for /random/"""
    counts = Counter(q['quotesource'] for q in files_data)
    return [[slug, counts[slug]] for slug in sorted(counts)]


# ===========
# tag and source helpers
# ===========


def tag_counts(files_data, min_count=1):
    counts = Counter(t for q in files_data for t in q['tags'] if t)
    return {t: c for t, c in counts.items() if c >= min_count}


def neighbours(tag, files_data, n=12):
    """the tags most often used together with `tag`, as (tag, count, percent
    of the top count), ranked by frequency (the old graph used the order
    the quotes happened to be read in)"""
    counts = Counter(t for q in files_data if tag in q['tags'] for t in q['tags'] if t and t != tag)
    top = counts.most_common(n)
    hi = top[0][1] if top else 1
    return [(t, c, int(100 * c / hi)) for t, c in top]


def tag_cloud(files_data, n=60):
    """the top `n` tags, alphabetical, each with a size step 1-5"""
    counts = tag_counts(files_data)
    top = sorted(counts.items(), key=lambda x: -x[1])[:n]
    if not top:
        return []
    hi, lo = top[0][1], top[-1][1]
    span = max(hi - lo, 1)
    return [(t, c, 1 + int(4 * (c - lo) / span)) for t, c in sorted(top, key=lambda x: x[0].lower())]


def tag_index(files_data, min_count=2):
    """tags grouped by initial: [('A', [(tag, count), ...]), ...]"""
    groups = OrderedDict()
    for t, c in sorted(tag_counts(files_data, min_count).items(), key=lambda x: x[0].lower()):
        initial = t[0].upper() if t[0].isalpha() else '#'
        groups.setdefault(initial, []).append((t, c))
    return list(groups.items())


def sources(files_data):
    """one row per source file: title, url, year saved, number of quotes"""
    rows = OrderedDict()
    for q in files_data:
        row = rows.setdefault(q['quotesource'], {
            'quotesource': q['quotesource'],
            'source': q['source'],
            'source_url': q['source_url'],
            'date': q['date'],
            'count': 0,
        })
        row['count'] += 1
    return list(rows.values())
