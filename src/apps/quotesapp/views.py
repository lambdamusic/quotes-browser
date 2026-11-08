#!/usr/bin/env python
# encoding: utf-8

from django.http.response import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlquote
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Q

import os
from time import strftime
import markdown
import random
import datetime
import itertools

from render_block import render_block_to_string
from myutils.myutils import printDebug
from settings import STATICFILES_DIRS, QUOTES_SOURCE_DIR

from .parser import *
from . import proto

APP = "quotesapp"



# ===========
# views with single landing page
# ===========


# def home(request):
# 	"""
# 	just an index of what's available  in /static for this app
# 	"""
# 	return redirect('/projects')



def about(request):
	"""
	bio page
	"""
	context = {}
	if proto.current_layout(request):
		return render(request, proto.template('about.html'), context)
	return render(request, APP + '/pages/about.html', context)



# ===========
# views for quotes
# ===========


def quote_detail(request, source_slug, quoteindex=1):
	"""
	Single quote view
	"""
	context = {}
	printDebug(f"VIEW ARGS: source_slug={source_slug}, quoteindex={quoteindex}")

	templatee = "detail-quotes.html"

	if request.user.is_superuser:
		admin_change_url = True
	else:
		admin_change_url = False

	quote_source_file = QUOTES_SOURCE_DIR+source_slug+".md"
	data = parse_markdown(quote_source_file)

	# get single quote using index
	try:
		this_quote = data[int(quoteindex)-1] 
	except:
		raise Http404
	
	this_quote = build_single_quote_dict(this_quote, source_slug)
	this_quote['quote_text'] = markdown.markdown(this_quote['markdown'], extensions=['fenced_code', 'codehilite'])
	
	print(f"Showing: \n\t=> {quote_source_file}\n")

	# get all MD contents from local directory for Tags Network
	files_data = read_all_files_data()

	if len(this_quote['tags']) > 1:
		random_tag = random.choice(this_quote['tags'])
		nodes, links = generate_graph_for_topic(random_tag, files_data)
	else:
		nodes, links = [], []

	# TODO pass object instead of fields
	context = {
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
		'admin_change_url': admin_change_url,
		'nodes': nodes,
		'links': links,
	}

	if proto.current_layout(request):
		proto.annotate(this_quote)
		same, prev, nxt = proto.siblings(this_quote, files_data)
		context.update({
			'quote': this_quote,
			'siblings': same,
			'prev': prev,
			'next': nxt,
			'related': proto.related(this_quote, files_data),
			'random_quote': proto.random_other(this_quote, files_data),
			'tag_sizes': proto.tag_sizes(this_quote['tags'], files_data),
		})
		return render(request, proto.template('quote.html'), context)
	
	return render(request, APP + '/pages/' + templatee, context)




def source_detail(request, source_slug):
	"""
	All quotes for a single source
	"""
	context = {}
	printDebug(f"VIEW ARGS: source_slug={source_slug}")

	templatee = "detail-source.html"

	if request.user.is_superuser:
		admin_change_url = True
	else:
		admin_change_url = False

	quote_source_file = QUOTES_SOURCE_DIR+source_slug+".md"
	data = parse_markdown(quote_source_file)
	tot_quotes = len(data)

	data_encoded = []
	# add rendered md for each quote included
	for el in data:
		quote = build_single_quote_dict(el, source_slug)
		quote['quote_text'] = markdown.markdown(quote['markdown'], extensions=['fenced_code', 'codehilite'])
		data_encoded.append(quote)

	# print(data_encoded)

	print(f"Showing: \n\t=> {quote_source_file}\n")

	# get all MD contents from local directory for Tags Network
	files_data = read_all_files_data()
	# random_tag = random.choice(data[0]['TAGS']) # TODO get tags from all quotes in this set, not just first one
	# nodes, links = generate_graph_for_topic(random_tag, files_data)

	context = {
		'return_items': data_encoded,
		'admin_change_url': admin_change_url,
		'quote_source_file': quote_source_file,
		'urlname': "source",
		'tot_quotes': tot_quotes,
	}

	if proto.current_layout(request):
		# tags from every quote in the source, not just the first one
		context['source_tags'] = sorted(proto.tag_counts(data_encoded).items(), key=lambda x: (-x[1], x[0].lower()))
		context['source'] = data_encoded[0] if data_encoded else None
		return render(request, proto.template('source.html'), context)

	return render(request, APP + '/pages/' + templatee, context)





def qa_quotes(request,):
	"""
	2024-11-28: Test view for development purposes
	(with a layout prototype on, the index of all sources instead)
	"""
	if proto.current_layout(request):
		return _proto_sources(request)

	context = {}

	query = request.GET.get('query', 'date')
	tag = request.GET.get('tag', None)
	format = request.GET.get('format', 'html')

	nodes, links, tags = [], [], []
	MIN_TAGS_OCCURRENCE = 1  # TODO in PROD it's 2
	
	if request.user.is_superuser:
		admin_change_url = True
	else:
		admin_change_url = False

	templatee = "quotes-qa.html"

	# get all MD contents from local directory
	files_data = read_all_files_data()
	tot_quotes = len(files_data)
	tot_sources = len(list(set([f['source'] for f in files_data])))

	# printDebug(files_data)

	context = {
		'return_items': files_data,
		'admin_change_url': admin_change_url,
		'urlname': "quotes",
		'query': query,
		'tag': tag,
		'tot_quotes': tot_quotes,
		'tot_sources': tot_sources,
	}

	
	return render(request, APP + '/pages/' + templatee, context)



def _proto_tags(request, context, files_data, tag):
	"""homepage, tag index and single tag page for the layout prototypes"""
	if tag:
		context['return_items'] = [proto.annotate(q) for q in files_data]
		context['neighbours'] = proto.neighbours(tag, files_data, n=16)
		return render(request, proto.template('tag.html'), context)

	if request.resolver_match.url_name == 'home':
		all_sources = proto.sources(files_data)
		context.update({
			'featured': proto.featured(files_data),
			'latest': proto.latest(files_data),
			'cloud': proto.tag_cloud(files_data),
			'tag_index': proto.tag_index(files_data, min_count=5),
			'top_sources': sorted(all_sources, key=lambda s: -s['count'])[:15],
			'tot_quotes': len(files_data),
			'tot_sources': len(all_sources),
			'tot_tags': len(proto.tag_counts(files_data)),
		})
		if context['featured']:
			context['random_quote'] = proto.random_other(context['featured'], files_data)
		return render(request, proto.template('home.html'), context)

	context.update({
		'tag_index': proto.tag_index(files_data, min_count=context['min_tags_occurrence']),
		'tot_tags': len(proto.tag_counts(files_data)),
	})
	return render(request, proto.template('tags.html'), context)



def _proto_sources(request):
	"""index of every source, for the layout prototypes"""
	files_data = read_all_files_data()
	order = request.GET.get('order', 'title')
	rows = proto.sources(files_data)
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
	return render(request, proto.template('sources.html'), context)




# ===========
# views for landing page
# ===========


def tags_all(request,):
	"""
	TODO
	"""
	context = {}

	query = request.GET.get('query', 'date')
	tag = request.GET.get('tag', None)
	format = request.GET.get('format', 'html')

	nodes, links, tags = [], [], []
	MIN_TAGS_OCCURRENCE = 2  # NOTE 
	
	if request.user.is_superuser:
		admin_change_url = True
	else:
		admin_change_url = False

	templatee = "tags.html"

	# get all MD contents from local directory
	files_data = read_all_files_data()
	
	if tag:
		# create local graph
		nodes, links = generate_graph_for_topic(tag, files_data)
		files_data = [f for f in files_data if tag in f['tags']] #override
		tot_quotes = len(files_data)
		tot_sources = len(list(set([f['source'] for f in files_data])))
		if not tot_quotes:
			raise Http404
	else:
		# full word cloud
		tags = count_tags(files_data)
		print(f"\nTags total: {len(tags)}")
		tags = sorted(tags.items()) # turn into a list
		tot_quotes, tot_sources = 0, 0 # not needed in this case

	context = {
		'return_items': files_data,
		'admin_change_url': admin_change_url,
		'urlname': "quotes",
		'query': query,
		'tag': tag,
		'tags': tags,
		'min_tags_occurrence': MIN_TAGS_OCCURRENCE,
		'nodes': nodes,
		'links': links,
		'tot_quotes': tot_quotes,
		'tot_sources': tot_sources,
	}

	if proto.current_layout(request):
		return _proto_tags(request, context, files_data, tag)
	
	return render(request, APP + '/pages/' + templatee, context)






##################################
###
# Support Functions
###
##################################



def generate_graph_for_topic(seed, files_data):
	"""gen graph data
	
	seed
		a tag
	files_data
		the full markdown files collection
	TODO
	Desc data structure 
	
	"""
	# return (None, None)
	
	first_level = calc_cooccurrent_topics(seed, files_data)
	
	#  create data for dataviz
	SIZE0, SIZE1, SIZE2 = 140, 70, 5
	green, lightgreen, yellow, lightorange, orange, red = 0, 0.4, 0.5, 0.6, 0.7, 0.8
	LVL0, LVL1, LVL2 = yellow, green, lightgreen  # templates uses this to determine color
	# LVL0, LVL1, LVL2 = orange, red, lightorange

	rels = calc_cooccurrent_topics(seed, files_data)
	# LINKS = [(x.subject1, x.subject2) for x in rels]

	LINKS_THRESHOLD_FIRST_LEVEL = 5
	LINKS_THRESHOLD_SECOND_LEVEL = 4

	LINKS = rels[:LINKS_THRESHOLD_FIRST_LEVEL]
	SEED = [(seed, SIZE0, LVL0)]
	NODES = [(x[1], SIZE1, LVL1) for x in LINKS]  # change with x.score
	NODES_AND_SEED = NODES + SEED  # add home entity by default, PS score drives color

	# second level
	for node in NODES:
		for x in calc_cooccurrent_topics(node[0], files_data)[:LINKS_THRESHOLD_SECOND_LEVEL]:
		# for x in node[0].is_subject_in_relations.all()[:5]:
			if x[1] not in [n[0] for n in NODES_AND_SEED]:
				NODES_AND_SEED += [(x[1], SIZE2, LVL2)]
			LINKS += [(x[0], x[1])]
	if False:
		for node in NODES:
			for x in node[0].is_subject_in_relations.all()[:5]:
				if x.subject2.id not in [n[0].id for n in NODES_AND_SEED]:
					NODES_AND_SEED += [(x.subject2, SIZE2, LVL2)]
				LINKS += [(x.subject1, x.subject2)]

	return (NODES_AND_SEED, LINKS)
	

def calc_cooccurrent_topics(tag, files_data):
	"""get all topics that co-occur with a given topic"""
	rels = []
	for f in files_data:
		if tag in f['tags']:
			for coocctag in f['tags']:
				if tag != coocctag and (tag, coocctag) not in rels:
					rels += [(tag, coocctag)]
	# print(rels)
	return rels


