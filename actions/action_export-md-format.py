#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
from dependencies.pyzotero import zotero
from dependencies import html2md

"""
This script exports a Markdown formatted, Chicago-style citation of the selected item.
"""

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Get the item key from the system input
item_key = alp.args()[0]
#item_key = '7VT63AQG'

# Return an HTML formatted citation in APA style
ref = zot.item(item_key, content='bib', style='chicago-author-date')

# Convert the HTML to Markdown
citation = html2md.html2text(ref[0]).encode('utf-8')

# Remove url, DOI, and "pp. ", if there
result = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
# Replace "_..._" MD italics with "*...*"
result = re.sub("_(.*?)_", "*\\1*", result)

# Pass the Markdown citation to output
print result
				