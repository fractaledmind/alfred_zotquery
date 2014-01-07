#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
from dependencies.pyzotero import zotero
from dependencies import html2md, alp

"""
This script exports a Markdown formatted, APA-style citation of the selected item.
"""

# Get the Library ID and API Key from the settings file
settings = alp.local(join="settings.json")
cache_file = open(settings, 'r')
data = json.load(cache_file)

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Get the item key from the system input
item_key = sys.argv[1]
#item_key = '7VT63AQG'

# Return an HTML formatted citation in APA style
ref = zot.item(item_key, content='bib', style='apa')

# Convert the HTML to Markdown
citation = html2md.html2text(ref[0]).encode('utf-8')

# Pass the Markdown citation to output
print citation