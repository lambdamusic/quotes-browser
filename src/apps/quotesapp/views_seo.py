#!/usr/bin/env python
# encoding: utf-8

"""
robots.txt and sitemap.xml. Both are fetched explicitly by tools/site-dump,
since wget only mirrors what pages link to.
"""

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from .parser import read_all_files_data


def robots_txt(request):
	lines = [
		"User-agent: *",
		"Allow: /",
		"",
		f"Sitemap: {settings.SITE_URL}/sitemap.xml",
	]
	return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def sitemap_xml(request):
	"""
	Every indexable page as its canonical URL (see components/base.html):
	https, trailing slash, no index.html, no query strings. lastmod is the
	latest date of the quotes on the page (modified, else saved).
	"""
	files_data = read_all_files_data()

	def when(q):
		return q['modified'] or q['date']

	urls = []  # (path, lastmod date or None)
	latest = max((when(q) for q in files_data if when(q)), default=None)
	for name in ['home', 'tags', 'sources']:
		urls.append((reverse('quotesapp:' + name), latest))
	urls.append((reverse('quotesapp:about'), None))

	tags, sources = {}, {}
	for q in files_data:
		d = when(q)
		urls.append((reverse('quotesapp:quotes', args=[q['quotesource'], q['quoteindex']]), d))
		sources[q['quotesource']] = max(filter(None, [sources.get(q['quotesource']), d]), default=None)
		for t in q['tags']:
			if t:
				tags[t] = max(filter(None, [tags.get(t), d]), default=None)
	for slug in sorted(sources):
		urls.append((reverse('quotesapp:source', args=[slug]), sources[slug]))
	for t in sorted(tags, key=str.lower):
		urls.append((reverse('quotesapp:tag', args=[t]), tags[t]))

	context = {'urls': [(settings.SITE_URL + path, lastmod) for path, lastmod in urls]}
	return render(request, 'quotesapp/sitemap.xml', context, content_type="application/xml")
