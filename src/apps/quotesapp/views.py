#!/usr/bin/env python
# encoding: utf-8

from django.http.response import Http404
from django.shortcuts import render

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
	return render(request, APP + '/pages/about.html', {})



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



# ===========
# views for quotes
# ===========


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
	}

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

	context = {
		'return_items': data_encoded,
		'admin_change_url': request.user.is_superuser,
		'quote_source_file': quote_source_file,
		'urlname': "source",
		'tot_quotes': len(data),
		# tags from every quote in the source, not just the first one
		'source_tags': sorted(helpers.tag_counts(data_encoded).items(), key=lambda x: (-x[1], x[0].lower())),
		'source': data_encoded[0] if data_encoded else None,
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
	}
	return render(request, APP + '/pages/sources.html', context)




# ===========
# views for landing page
# ===========


def tags_all(request,):
	"""
	The homepage, the index of all tags, and a single tag (?tag=)
	"""
	tag = request.GET.get('tag', None)
	MIN_TAGS_OCCURRENCE = 2  # NOTE

	# get all MD contents from local directory
	files_data = read_all_files_data()

	if tag:
		tag_quotes = [helpers.annotate(f) for f in files_data if tag in f['tags']]
		if not tag_quotes:
			raise Http404
		context = {
			'return_items': tag_quotes,
			'tag': tag,
			'neighbours': helpers.neighbours(tag, files_data, n=16),
			'tot_quotes': len(tag_quotes),
			'tot_sources': len(set(f['source'] for f in tag_quotes)),
		}
		return render(request, APP + '/pages/tag.html', context)

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
		}
		return render(request, APP + '/pages/home.html', context)

	context = {
		'tag_index': helpers.tag_index(files_data, min_count=MIN_TAGS_OCCURRENCE),
		'tot_tags': len(helpers.tag_counts(files_data)),
		'min_tags_occurrence': MIN_TAGS_OCCURRENCE,
	}
	return render(request, APP + '/pages/tags.html', context)
