#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
from dependencies.pyzotero import zotero
from dependencies import html2md


"""
This script exports a Bibliography of Markdown formatted, Chicago-style citations for the selected collection.
"""

inp = alp.args()[0].split(':')
#inp = 'c:GXWGBRJD'.split(':')

# Get the Library ID and API Key from the settings file
with open(alp.local(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# If a Collection
if inp[0] == 'c':
	
	# Get the item key from the system input
	coll_key = inp[1]
	#coll_key = 'GXWGBRJD'

	# Return a list of HTML formatted citations in Chicago style
	cites = zot.collection_items(coll_key, content='bib', style='chicago-author-date')
	
	md_cites = []
	for ref in cites:
		# Convert the HTML to Markdown
		citation = html2md.html2text(ref).encode('utf-8')

		# Remove url, DOI, and "pp. ", if there
		result = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
		# Replace "_..._" MD italics with "*...*"
		result = re.sub("_(.*?)_", "*\\1*", result)

		# Append the Markdown citation to a new list
		md_cites.append(result)

	# Sort that list alphabetically
	sorted_md = sorted(md_cites)
	# Begin with WORKS CITED header
	sorted_md.insert(0, 'WORKS CITED\n')

	# Output the result as a well-formatted string
	print '\n'.join(sorted_md)


elif inp[0] == 't':

	# Get the item key from the system input
	tag_key = inp[1]
	#coll_key = 'Hippocrates'

	# Return a list of HTML formatted citations in Chicago style
	cites = zot.tag_items(tag_key, content='bib', style='chicago-author-date')

	md_cites = []
	for ref in cites:
		# Convert the HTML to Markdown
		citation = html2md.html2text(ref).encode('utf-8')

		# Remove url, DOI, and "pp. ", if there
		result = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
		# Replace "_..._" MD italics with "*...*"
		result = re.sub("_(.*?)_", "*\\1*", result)

		# Append the Markdown citation to a new list
		md_cites.append(result)

	# Sort that list alphabetically
	sorted_md = sorted(md_cites)
	# Begin with WORKS CITED header
	sorted_md.insert(0, 'WORKS CITED\n')

	# Output the result as a well-formatted string
	print '\n'.join(sorted_md)
