"""

Quotes Helper Scripts

$ python manage.py quotes_helper 2

NOTE: the tags modifiers need to be rerun a couple of times for all changes to be applied.

"""


from django.core.management.base import BaseCommand, CommandError

import os
import datetime
from django.utils import timezone

from libs.myutils.myutils import slugify
from quotesapp.views import count_tags, read_all_files_data, QUOTES_SOURCE_DIR

# take the path used by webapp / override here is needed for testing purposes
QUOTES_PATH = QUOTES_SOURCE_DIR



class Command(BaseCommand):
	help = """Scripts for Quotes MD. """

	def add_arguments(self, parser):

		# NOTE INHERITED FROM BASECOMMAND CLASS
		# parser.add_argument(
		#     '-v', '--verbosity', action='store', dest='verbosity', default=1,
		#     type=int, choices=[0, 1, 2, 3],
		#     help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output',
		# )

		# Positional arguments
		parser.add_argument('script_number', nargs='+', type=int)

		parser.add_argument(
			'--verbose',
			action='store_true',
			help='Verbose mode',
		)

	def handle(self, *args, **options):
		
		verbose = options['verbose']
		LOCK = True

		print(f"==> QUOTES_PATH: {QUOTES_PATH}")

		#################
		# SCRIPT 1: remove tags with count of 1
		# Files are modified and overwritten
		#################
		if 1 in options['script_number']:
			print("==> SCRIPT 1: remove tags with count of 1")

			# read all tags available 
			tags = count_tags(read_all_files_data())

			# Filter dictionary by keeping elements whose keys are divisible by 2
			badtags = dict(filter(lambda elem: elem[1] == 1, tags.items()))
			badtags = [f"#{x}" for x in list(badtags.keys())]
			# print(badtags)
			# return

			# update all files
			for f in os.listdir(QUOTES_PATH):
				if f.endswith(".md"):
					if not LOCK: do_remove_tags(f, badtags, False, verbose)


		#################
		# SCRIPT 2: remove tags by passing a list of tags
		# Files are modified and overwritten
		#################
		if 2 in options['script_number']:
			print("==> SCRIPT 2: remove tags by passing a list of tags")

			# MANUALLY define tags to remove	
			badtags = ["#ChE", "#DA", "#IL", "#LE", "#LA" "#PO", "#c", "#ty", "#Chi", "#Non", "#GLI", "#di", "#Quella", "#SIA", "#La", "#Ma", "#PI", "#PO", "#PUR", "#VOI", "#way"]
			badtags = ["#exchange", "#origin", "#ROM", "#qui", "#sono", "#ECCO", "#mammae", "#tutti", "#SUA", "#Noi", "#Se", "#more-trouble", "#support", "#part"]

			# update all files
			for f in os.listdir(QUOTES_PATH):
				if f.endswith(".md"):
					if not LOCK: do_remove_tags(f, badtags, False, verbose)



		#################
		# SCRIPT 3: merge files that come from same source - 2024-12-01
		# NOTE This skips anything that has no title or no source!!!!!
		#################
		if 3 in options['script_number']:
			print("==> SCRIPT 3: merge files")

			quotes_from_files_data = read_all_files_data()
			# group by source
			data_by_source = {}
			for q in quotes_from_files_data:
				if q['source'] not in data_by_source:
					data_by_source[q['source']] = [q]
				else:
					if q['quoteindex'] == 1: # increment automatically
						q['quoteindex'] = len(data_by_source[q['source']]) + 1
					data_by_source[q['source']].append(q)

			# rebuild files
			output_path = "/Users/michele.pasin/tmp/quotes-reformat/"

			for x in data_by_source:
				q1 = data_by_source[x][0]
				date = q1['date']
				filename = f'{date}-{"-".join([x for x in slugify(x).split("-")[:10]])}.md' 
		
				print(filename, ">>quotes:", len(data_by_source[x]), [y['quoteindex'] for y in data_by_source[x]])

				header = f"""---
template: quote-multi.html
source: "{q1['source']}"
url: {q1['source_url']}
date: {q1['date']}
modified: {q1['modified'] or q1['date']}
review: {q1['review']}
---"""
				# build header from first quotes, as default
				if False: # LOCK
					with open(output_path+filename, "w") as f:
						f.write(header)

						for q in data_by_source[x]: # for each quote in source
							f.write(f"\n\n# {q['title']}")
							f.write(f"""\n{" ".join(["#"+t for t in q['tags']])}""")
							if q['markdown'].startswith("\n"):
								q['markdown'] = q['markdown'][1:]
							f.write(f"\n{q['markdown']}")


			print("---\nTotal unique sources: ", len(data_by_source))


		#################


		print("----------\nDone")






##
##
##
# HELPERS
##
##
##





def do_remove_tags(fname, tags, trial_run=False, verbose=True):
	"""
	"""

	# opening the file in read mode
	file = open(QUOTES_PATH+fname	, "r")
	replacement = ""

	def replace_with_empty(tag, replaceval, line, fname):
		print("Reading file: "+fname)
		print("\tRemoving: "+tag)
		return line.replace(tag, replaceval)

	# ensure tags format
	for tag in tags:
		if not tag.startswith("#"):
			print("\tERROR: all tags should start with #!", tag)
			return

	# using a for loop to read each line of the file
	for line in file:
		line = line.strip()
		linecopy = line
		if line.startswith("#"):
			for tag in tags:
				# edge cases: tag at beginning and end of line!
				if line.startswith(tag + " "):
					linecopy = replace_with_empty(tag + " ", " ", line, fname)
				elif line.endswith(" " + tag):
					linecopy = replace_with_empty(" " + tag, " ", line, fname)
				else:
					tag = f" {tag} " # add space to avoid false positive
					if tag in line:
						linecopy = replace_with_empty(tag, " ", line, fname)

		replacement = replacement + linecopy + "\n"

	file.close()
	
	if not trial_run:
		# opening the file in write mode
		fout = open(QUOTES_PATH+fname, "w")
		fout.write(replacement)
		fout.close()


