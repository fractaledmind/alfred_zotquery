#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import os.path
from dependencies.pyzotero import zotero
from _zotquery import setClipboardData

"""
This script exports a Bibliography for the selected collection in the preferred style and format.
"""

#inp = alp.args()[0].split(':')
inp = 'c:GXWGBRJD'.split(':')

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Get the user's export preferences
with open(alp.storage(join="prefs.json"), 'r') as f:
	prefs = json.load(f)
	f.close()

# Create files, if necessary
if not os.path.exists(alp.cache(join='full_bibliography.html')):
	with open(alp.cache(join='full_bibliography.html'), 'w') as f:
		f.write('')
		f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# If a Collection
if inp[0] == 'c':
	# Get the item key from the system input
	coll_key = inp[1]
	#coll_key = 'GXWGBRJD'

	# Return a list of HTML formatted citations in preferred style
	cites = zot.collection_items(coll_key, content='bib', style=prefs['csl'])
	
elif inp[0] == 't':
	# Get the item key from the system input
	tag_key = inp[1]
	#tag_key = 'Hippocrates'

	# Return a list of HTML formatted citations in preferred style
	cites = zot.tag_items(tag_key, content='bib', style=prefs['csl'])

# Export in chosen format
if prefs['format'] == 'Markdown':
	from dependencies import html2md
	import re

	md_cites = []
	for ref in cites:

		html_ref = ref.encode('ascii', 'xmlcharrefreplace')

		# Convert the HTML to Markdown
		citation = html2md.html2text(html_ref)

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

	# Pass the Markdown bibliography to clipboard
	setClipboardData('\n'.join(sorted_md))

	print "Markdown"

elif prefs['format'] == 'Rich Text':
	from dependencies import applescript
	import re

	# Write html to temporary bib file
	with open(alp.cache(join="full_bibliography.html"), 'w') as f:
		for ref in cites:
			f.write(ref.encode('ascii', 'xmlcharrefreplace'))
			f.write('<br>')
		f.close()

	# Read and clean-up html
	with open(alp.cache(join="full_bibliography.html"), 'r+') as f:
		bib_html = f.read()
		no_links = re.sub("http(.*?)\\.(?=<)", "", bib_html)
		no_dois = re.sub("doi(.*?)\\.(?=<)", "", no_links)
		clean_html = re.sub("pp. ", "", no_dois)
		clean_html.insert(0, 'WORKS CITED<br>')
		
	# Write cleaned-up html back to bib file
	with open(alp.cache(join="full_bibliography.html"), 'w') as f:
		f.write(clean_html)
		f.close()

	# Convert html to RTF and copy to clipboard
	a_script = """
		do shell script "textutil -convert rtf " & quoted form of "%s" & " -stdout | pbcopy"
		""" % alp.cache(join="full_bibliography.html")
	applescript.asrun(a_script)

	# Write blank file to bib file
	with open(alp.cache(join="full_bibliography.html"), 'w') as f:
		f.write('')
		f.close()

	print "Rich Text"
