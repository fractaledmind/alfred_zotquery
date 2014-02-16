#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
from dependencies.pyzotero import zotero
from _zotquery import setClipboardData

"""
This script copies to the clipboard a reference to the selected item in the preferred style and format.
"""

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Get the user's export preferences
with open(alp.storage(join="prefs.json"), 'r') as f:
	prefs = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Get the item key from the system input
item_key = alp.args()[0]
#item_key = 'NKT78PX8'

# Return an HTML formatted citation in preferred style
ref = zot.item(item_key, content='citation', style=prefs['csl'])

# Remove the <span>...</span> tags
clean_ref = ref[0][6:-7]

# Export in chosen format
if prefs['format'] == 'Markdown':
	from dependencies import html2md

	# Convert the HTML to Markdown
	citation = html2md.html2text(clean_ref)

	# Pass the Markdown citation to clipboard
	setClipboardData(citation[0:-1])

	print "Markdown"

elif prefs['format'] == 'Rich Text':
	from dependencies import applescript

	# Write html to temporary file
	with open(alp.cache(join="temp.html"), 'w') as f:
		f.write(clean_ref.encode('ascii', 'xmlcharrefreplace'))
		f.close

	# Convert html to RTF and copy to clipboard
	a_script = """
		do shell script "textutil -convert rtf " & quoted form of "%s" & " -stdout | pbcopy"
		""" % alp.cache(join='temp.html')
	applescript.asrun(a_script)

	print "Rich Text"
