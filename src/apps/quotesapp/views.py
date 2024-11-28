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

APP = "quotesapp"



# ===========
# views with single landing page
# ===========


def home(request):
	"""
	just an index of what's available  in /static for this app
	"""
	return redirect('/projects')



def about(request):
	"""
	bio page
	"""
	context = {}
	return render(request, APP + '/pages/about.html', context)



# ===========
# views with single landing page
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
	MIN_TAGS_OCCURRENCE = 1  # TODO in PROD it's 2
	
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
	
	return render(request, APP + '/pages/' + templatee, context)




def quote_detail(request, slug, orderno=None):
	"""
	TODO
	"""
	context = {}
	printDebug(f"VIEW: order={orderno}")

	templatee = "detail-quotes.html"

	if request.user.is_superuser:
		admin_change_url = True
	else:
		admin_change_url = False

	quote_source_file = QUOTES_SOURCE_DIR+slug+".md"
	data = parse_markdown(quote_source_file)
	this_quote = data[0] # TEMP TILL WE FIX ORDER INFO
	# TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN = data[0]
	html_quote_text = markdown.markdown(this_quote['PURE_MARKDOWN'], extensions=['fenced_code', 'codehilite'])

	print(f"Showing: \n\t=> {quote_source_file}\n")

	# get all MD contents from local directory for Tags Network
	files_data = read_all_files_data()
	random_tag = random.choice(this_quote['TAGS'])
	nodes, links = generate_graph_for_topic(random_tag, files_data)

	context = {
		'quote_text': html_quote_text,
		'quote_source_file': quote_source_file,
		'title': this_quote['TITLE'],
		'tags': this_quote['TAGS'],
		'source': this_quote['SOURCE'],
		'source_url': this_quote['SOURCE_URL'],
		'created': this_quote['CREATED'],
		'modified': this_quote['MODIFIED'],
		'admin_change_url': admin_change_url,
		'nodes': nodes,
		'links': links,
	}

	
	return render(request, APP + '/pages/' + templatee, context)




def qa_quotes(request,):
	"""
	2024-11-28: Test view for development purposes
	"""
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


