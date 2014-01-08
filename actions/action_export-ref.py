#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import re
from dependencies.pyzotero import zotero
from dependencies import alp

"""
This script exports a Markdown formatted, APA-style reference (i.e. Author Date) of the selected item.
"""

# Get the Library ID and API Key from the settings file
settings = alp.local(join="settings.json")
cache_file = open(settings, 'r')
data = json.load(cache_file)

try:
	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	# Get the item key from the system input
	item_key = sys.argv[1]
	#item_key = '7VT63AQG'

	# Return an HTML formatted reference in APA style
	ref = zot.item(item_key, content='citation', style='chicago-author-date')

	# Remove the <span>...</span> tags
	clean_ref = ref[0][6:-7]

	# Change from (Author Date) to Author (Date)
	result = re.sub(r"\((.*?)\s(.*?)\)", "\\1 (\\2)", clean_ref)

	# Pass the reference to output
	print result
except:
	print 'Error! Not connected to internet.'