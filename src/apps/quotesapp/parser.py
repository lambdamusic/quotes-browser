#!/usr/bin/env python
# encoding: utf-8

"""
Utils to parse the markdown of quotes and return structured data to the app
"""


import os
from time import strftime
import markdown
import random
import datetime
import itertools

from myutils.myutils import printDebug
from settings import STATICFILES_DIRS, QUOTES_SOURCE_DIR



def read_all_files_data():
	"""
	Reads MD files

	If tag is provided, return only matching files.

	Returns a list of dicts with the following keys:
		title
		filename
		tags
		review
	"""
	counter1, counter2, counter3 = 0, 0, 0
	files_data = []
	VERBOSE = True # debugging only
 
	for filename in os.listdir(QUOTES_SOURCE_DIR):
		counter1 +=1
		if "-" in filename and filename.endswith(".md"):

			counter2 +=1
			quote =  {}

			results = parse_markdown(QUOTES_SOURCE_DIR+"/"+filename, VERBOSE)

			for r in results:
				TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN = r
				if TITLE:

					quote['filename'] = filename
					quote['title'] = TITLE
					quote['tags'] = TAGS
					quote['source'] = SOURCE
					quote['source_url'] = SOURCE_URL
					quote['review'] = REVIEW

					if SOURCE:
						counter3 +=1
						files_data += [quote]

	# finally
	files_data = sorted(files_data, key= lambda x: x['source'])
	printDebug(f"""\n# Files read: {counter1}\n# Records parsed: {counter2}\n# Records selected: {counter3}\n""", "bold")
	return(files_data)





def count_tags(files_data):
	"""
	Quick count of quotes per tags

	Return a dict EG
	 {'such-benefits': 1, 'relata': 1, 'notion-of-sign': 1, 'true-self': 1, 'recognition': 1}
	"""
	tags = {}
	for quote in files_data:
		for tag in quote['tags']:
			if str(tag) not in tags:
				tags[str(tag)] = 1
			else:
				tags[str(tag)] += 1
	return tags




def parse_markdown(full_file_path, verbose=False): 
	"""Parse the Quote markdown and return title and other metadata. 

	"""

	DEBUG_TAGS = False

	if verbose: printDebug("Parsing..: \n" + full_file_path)
	with open(full_file_path) as f:
		lines = f.readlines()
		# print(lines[1], lines[2])
		# check top of file for header markup
		if "template: quote-multi.html" in lines[1] or "template: quote-multi.html" in lines[2]:
			print("multi")
			return _parse_markdown_multi(lines, full_file_path, verbose=verbose)
		elif "template: quote.html" in lines[1] or "template: quote.html" in lines[2]:
			return _parse_markdown_single(lines, full_file_path, verbose=verbose)		
		else:
			printDebug(f"ERROR: file has no supported header.. skipping {full_file_path}")
			return []



def _parse_markdown_single(lines, full_file_path, verbose=False): 
	"""Parse the Obsidian markdown and return title and other metadata. 

	EG 
	```
---
template: quote.html
title: "Instance of a property"
source: "Cidoc-crm Version 4.2.4 - Reference Document"
url: http://www.google.co.uk/url?sa=t&rct=j&q=cidoc-crm%20version%204.2.4%20-%20reference%20document&source=web&cd=1&ved=0CEMQFjAA&url=http%3A%2F%2Fwww.cidoc-crm.org%2Fprevious_releases_cidoc.html&ei=xjnMT
date: 2013-02-26
modified: 2015-05-04
review: false
---
#properties #factual-relation #instances #relation #range #intension


	==This is where the markdown content starts..==
	```

	"""

	DEBUG_TAGS = False

	if verbose: printDebug("...quote template: SINGLE")

	text_begins_flag = tag_flag = 0
	TITLE, SOURCE, SOURCE_URL, PURE_MARKDOWN = "", "", "", ""
	REVIEW = False
	DATE, MODIFIED = None, None
	TAGS = []
	for l in lines:
		# printDebug(l)
		if tag_flag and text_begins_flag == 2:
			PURE_MARKDOWN += l
		elif l == "---\n":
			text_begins_flag += 1  # after second one, the header is over
		elif l.strip().startswith("#"):
			tag_flag = 1
			tags = [x.replace("#", "") for x in l.strip().split()]
			if DEBUG_TAGS: print(f"Tags: {tags}")
			TAGS = tags
		elif l.startswith("title: "):
			TITLE = l.replace("title: ", "")[1:-2] # remove quotes and newline char
		elif l.startswith("source: "):
			SOURCE = l.replace("source: ", "")[1:-2] # remove quotes and newline char
		elif l.startswith("url: "):
			SOURCE_URL = l.replace("url: ", "")[0:-1] # remove newline char
		elif l.startswith("review: "):
			if "true" in l:
				REVIEW = True
		elif l.startswith("date: "):
			DATE = l.replace("date: ", "") 
			if DATE[0] == "\"":
				DATE = DATE[1:-2] # remove quotes and newline char
			else:
				DATE = DATE[:-1] # remove newline char
			DATE = datetime.datetime.strptime(DATE, "%Y-%m-%d")
			DATE = DATE.replace(tzinfo=datetime.timezone.utc).date()
		elif l.startswith("modified: "):
			MODIFIED = l.replace("modified: ", "") 
			if MODIFIED[0] == "\"":
				MODIFIED = MODIFIED[1:-2] # remove quotes and newline char
			else:
				MODIFIED = MODIFIED[:-1] # remove newline char
			MODIFIED = datetime.datetime.strptime(MODIFIED, "%Y-%m-%d")
			MODIFIED = MODIFIED.replace(tzinfo=datetime.timezone.utc).date()
	
	return [[TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN]]
	






def _parse_markdown_multi(lines, full_file_path, verbose=False): 
	"""Parse the Obsidian markdown and return title and other metadata. 
	For multi quote files 

	2024-11-27 TODO TODO TODO

	EG 
	```
---
template: quote-multi.html
source: "Is BI dead?"
source_year: 2020
url: https://benn.substack.com/p/is-bi-dead
date: 2022-09-28
review: false
---

# BI tools limitations
#dashboard #BI #visualization #story #text #game #character #interactive-fiction
..if a metric on a dashboard falls below some threshold, absolutely, send an email. But BI tools aren’t pipelines. They’re borders, handing off data between machines and humans. People read data diff

	```

	"""

	DEBUG_TAGS = False

	if verbose: printDebug("...quote template: MULTI")

	text_begins_flag = tag_flag = 0
	TITLE, SOURCE, SOURCE_URL, PURE_MARKDOWN = "", "", "", ""
	REVIEW = False
	DATE, MODIFIED = None, None
	TAGS = []
	results = []
	for l in lines:
		# printDebug(l)

		if text_begins_flag < 2: # we are in the header

			if l == "---\n":
				text_begins_flag += 1  # after second one, the header is over
			elif l.startswith("source: "):
				SOURCE = l.replace("source: ", "")[1:-2] # remove quotes and newline char
			elif l.startswith("url: "):
				SOURCE_URL = l.replace("url: ", "")[0:-1] # remove newline char
			elif l.startswith("source_year: "):
				SOURCE_YEAR = l.replace("source_year: ", "")[1:-2] # remove quotes and newline char
			elif l.startswith("review: "):
				if "true" in l:
					REVIEW = True
			elif l.startswith("date: "):
				DATE = l.replace("date: ", "") 
				if DATE[0] == "\"":
					DATE = DATE[1:-2] # remove quotes and newline char
				else:
					DATE = DATE[:-1] # remove newline char
				DATE = datetime.datetime.strptime(DATE, "%Y-%m-%d")
				DATE = DATE.replace(tzinfo=datetime.timezone.utc).date()
			elif l.startswith("modified: "):
				MODIFIED = l.replace("modified: ", "") 
				if MODIFIED[0] == "\"":
					MODIFIED = MODIFIED[1:-2] # remove quotes and newline char
				else:
					MODIFIED = MODIFIED[:-1] # remove newline char
				MODIFIED = datetime.datetime.strptime(MODIFIED, "%Y-%m-%d")
				MODIFIED = MODIFIED.replace(tzinfo=datetime.timezone.utc).date()

		else: # we are in the quotes section

			if TITLE:
				# printDebug(TITLE)
				PURE_MARKDOWN += l
			elif l.strip().startswith("# "): # new title: push previously found
				if PURE_MARKDOWN:
					printDebug("Appending: line 263")
					results.append([TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN])
					PURE_MARKDOWN, TAGS = "", []
				TITLE = l.replace("# ", "")[0:-1] # remove quotes and newline char
			elif l.strip().startswith("## "): # new title: push previously found
				if PURE_MARKDOWN:
					results.append([TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN])
					PURE_MARKDOWN, TAGS = "", []
				TITLE = l.replace("# ", "")[1:-2] # remove quotes and newline char
			elif l.strip().startswith("#"):
				tag_flag = 1
				tags = [x.replace("#", "") for x in l.strip().split()]
				if DEBUG_TAGS: print(f"Tags: {tags}")
				TAGS = tags

	# finally : catch last quote or single qupte
	if TITLE and PURE_MARKDOWN:
		printDebug("Appending: line 280")
		results.append([TITLE, SOURCE, SOURCE_URL, DATE, MODIFIED, REVIEW, TAGS, PURE_MARKDOWN])


	printDebug(f"Results size: {len(results)} \n {results}")
	return results
	