#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
import os.path
from pyzotero import zotero
from _zotquery import to_unicode

"""
This script appends a citation to a temporary bibliography file in the preferred style and format.
"""

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Get the user's export preferences
with open(alp.storage(join="prefs.json"), 'r') as f:
	prefs = json.load(f)
	f.close()

# Create files, if necessary
if not os.path.exists(alp.cache(join='temp_bibliography.html')):
	with open(alp.cache(join='temp_bibliography.html'), 'w') as f:
		f.write('')
		f.close()

if not os.path.exists(alp.cache(join='temp_bibliography.txt')):
	with open(alp.cache(join='temp_bibliography.txt'), 'w') as f:
		f.write('')
		f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Get the item key from the system input
item_key = alp.args()[0]
#item_key = 'BTRCZ88H'

# Return an HTML formatted citation in preferred style
ref = zot.item(item_key, content='bib', style=prefs['csl'])

uref = to_unicode(ref[0], encoding='utf-8')
html_ref = uref.encode('ascii', 'xmlcharrefreplace')

# Remove url, DOI, and "pp. ", if there
clean_ref = re.sub("(?:http|doi)(.*?)$|pp. ", "", html_ref)

# Export in chosen format
if prefs['format'] == 'Markdown':
	from dependencies import html2md

	# Convert the HTML to Markdown
	citation = html2md.html2text(clean_ref)

	# Replace "_..._" MD italics with "*...*"
	result = re.sub("_(.*?)_", "*\\1*", citation)

	# Append final, formatted input to biblio file
	with open(alp.cache(join='temp_bibliography.txt'), 'a') as f:
		f.write(result[0:-1])
		f.write('\n\n')
		f.close()

	print "Markdown"
	
elif prefs['format'] == 'Rich Text':

	# Write html to temporary file
	with open(alp.cache(join="temp_bibliography.html"), 'a') as f:
		f.write(clean_ref[23:])
		f.write('<br>')
		f.close

	print "Rich Text"
