#!/usr/bin/env python
# encoding: utf-8

from collections import OrderedDict

from django.http.response import Http404
from django.shortcuts import render
from django.urls import reverse

import markdown

from myutils.myutils import printDebug
from settings import QUOTES_SOURCE_DIR

from .parser import *
from . import helpers

APP = "quotesapp"



# ===========
# views with single landing page
# ===========



def about(request):
	"""
	bio page
	"""
	context = {
		'og_title': 'About',
		'meta_description': 'About this commonplace book: passages Michele Pasin saved while reading books, papers and web pages since 2013, kept as plain markdown files.',
	}
	return render(request, APP + '/pages/about.html', context)



def random_quote(request):
	"""
	picks a quote in the browser (see pages/random.html), so it stays random
	on the static mirror
	"""
	files_data = read_all_files_data()
	context = {
		'counts': helpers.quote_counts(files_data),
		'tot_quotes': len(files_data),
	}
	return render(request, APP + '/pages/random.html', context)



def not_found(request):
	"""
	/404.html, which GitHub Pages serves for any missing page. A 200 here,
	since wget only saves pages that load (fetched explicitly by site-dump)
	"""
	return render(request, APP + '/pages/404.html', {})



# ===========
# views for quotes
# ===========


def _graph(request, seeds, files_data, n):
	"""the tag graph for the right-hand column (helpers.tag_graph,
	components/_graph.html), each tag with its page's URL"""
	graph = helpers.tag_graph(seeds, files_data, n=n)
	for node in graph['nodes']:
		node['url'] = reverse('quotesapp:tag', args=[node['id']])
	return {'graph': graph}



def quote_detail(request, source_slug, quoteindex=1):
	"""
	Single quote view
	"""
	printDebug(f"VIEW ARGS: source_slug={source_slug}, quoteindex={quoteindex}")

	quote_source_file = QUOTES_SOURCE_DIR+source_slug+".md"
	data = parse_markdown(quote_source_file)

	# get single quote using index
	try:
		this_quote = data[int(quoteindex)-1]
	except:
		raise Http404

	this_quote = build_single_quote_dict(this_quote, source_slug)
	this_quote['quote_text'] = markdown.markdown(this_quote['markdown'], extensions=['fenced_code', 'codehilite'])
	helpers.annotate(this_quote)

	print(f"Showing: \n\t=> {quote_source_file}\n")

	# all quotes, for related ones and previous/next in the source
	files_data = read_all_files_data()
	same, prev, nxt = helpers.siblings(this_quote, files_data)

	# TODO pass object instead of fields
	context = {
		'quote': this_quote,
		'quote_text': this_quote['quote_text'],
		'quote_source_file': quote_source_file,
		'title': this_quote['title'],
		'tags': this_quote['tags'],
		'quoteindex': this_quote['quoteindex'],
		'quotesource': this_quote['quotesource'],
		'source': this_quote['source'],
		'source_url': this_quote['source_url'],
		'created': this_quote['date'],
		'modified': this_quote['modified'],
		'admin_change_url': request.user.is_superuser,
		'siblings': same,
		'prev': prev,
		'next': nxt,
		'related': helpers.related(this_quote, files_data),
		'og_title': this_quote['title'],
		'og_type': 'article',
		'meta_description': helpers.shorten(this_quote['plain'], 155),
		'jsonld': helpers.quote_jsonld(this_quote, request.path),
	}
	if [t for t in this_quote['tags'] if t]:
		context.update(_graph(request, this_quote['tags'][:6], files_data, n=10))

	return render(request, APP + '/pages/quote.html', context)




def source_detail(request, source_slug):
	"""
	All quotes for a single source
	"""
	printDebug(f"VIEW ARGS: source_slug={source_slug}")

	quote_source_file = QUOTES_SOURCE_DIR+source_slug+".md"
	data = parse_markdown(quote_source_file)

	data_encoded = []
	# add rendered md for each quote included
	for el in data:
		quote = build_single_quote_dict(el, source_slug)
		quote['quote_text'] = markdown.markdown(quote['markdown'], extensions=['fenced_code', 'codehilite'])
		data_encoded.append(quote)

	print(f"Showing: \n\t=> {quote_source_file}\n")

	source = data_encoded[0] if data_encoded else None
	context = {
		'return_items': data_encoded,
		'admin_change_url': request.user.is_superuser,
		'quote_source_file': quote_source_file,
		'urlname': "source",
		'tot_quotes': len(data),
		# tags from every quote in the source, not just the first one
		'source_tags': sorted(helpers.tag_counts(data_encoded).items(), key=lambda x: (-x[1], x[0].lower())),
		'source': source,
		'og_title': source['source'] if source else None,
		'meta_description': helpers.source_description(data_encoded) if source else None,
	}

	return render(request, APP + '/pages/source.html', context)




def sources(request):
	"""
	index of every source, by title, number of quotes or date saved
	"""
	files_data = read_all_files_data()
	order = request.GET.get('order', 'title')
	rows = helpers.sources(files_data)
	if order == 'count':
		rows = sorted(rows, key=lambda s: -s['count'])
	elif order == 'date':
		rows = sorted(rows, key=lambda s: str(s['date']), reverse=True)
	else:
		rows = sorted(rows, key=lambda s: s['source'].lower())
	context = {
		'return_items': rows,
		'order': order,
		'tot_quotes': len(files_data),
		'og_title': 'Sources',
		'meta_description': f'All {len(rows)} sources of the {len(files_data)} quotes: books, papers and web pages, by title, number of quotes or date saved.',
	}
	return render(request, APP + '/pages/sources.html', context)




# ===========
# views for landing page
# ===========


def tag_detail(request, tag):
	"""
	A single tag: its quotes grouped by source
	"""
	files_data = read_all_files_data()
	tag_quotes = [helpers.annotate(f) for f in files_data if tag in f['tags']]
	if not tag_quotes:
		raise Http404
	sources = list(OrderedDict.fromkeys(f['source'] for f in tag_quotes))
	context = {
		'return_items': tag_quotes,
		'tag': tag,
		'neighbours': helpers.neighbours(tag, files_data, n=16),
		'tot_quotes': len(tag_quotes),
		'tot_sources': len(sources),
		'og_title': f'#{tag}',
		'meta_description': helpers.tag_description(tag, tag_quotes, sources),
	}
	context.update(_graph(request, [tag], files_data, n=14))
	return render(request, APP + '/pages/tag.html', context)



def tags_all(request,):
	"""
	The homepage and the index of all tags. A single tag used to be ?tag=x;
	that URL now renders a redirect page to /tags/x/, so the old mirrored
	files (tags/index.html%3Ftag=x.html) keep working (see tools/tag-redirects)
	"""
	tag = request.GET.get('tag', None)
	MIN_TAGS_OCCURRENCE = 2  # NOTE

	# get all MD contents from local directory
	files_data = read_all_files_data()

	if tag:
		known = tag in helpers.tag_counts(files_data)
		target = reverse('quotesapp:tag', args=[tag]) if known else reverse('quotesapp:tags')
		return render(request, APP + '/pages/redirect.html', {'target': target})

	if request.resolver_match.url_name == 'home':
		all_sources = helpers.sources(files_data)
		context = {
			'featured': helpers.featured(files_data),
			'latest': helpers.latest(files_data),
			'cloud': helpers.tag_cloud(files_data),
			'top_sources': sorted(all_sources, key=lambda s: -s['count'])[:8],
			'tot_quotes': len(files_data),
			'tot_sources': len(all_sources),
			'tot_tags': len(helpers.tag_counts(files_data)),
			'jsonld': helpers.website_jsonld(),
		}
		return render(request, APP + '/pages/home.html', context)

	tot_tags = len(helpers.tag_counts(files_data))
	context = {
		'tag_index': helpers.tag_index(files_data, min_count=MIN_TAGS_OCCURRENCE),
		'tot_tags': tot_tags,
		'min_tags_occurrence': MIN_TAGS_OCCURRENCE,
		'og_title': 'Tags',
		'meta_description': f'All {tot_tags} tags in the commonplace book, A to Z: the topics of {len(files_data)} quotes from books, papers and web pages.',
	}
	return render(request, APP + '/pages/tags.html', context)
