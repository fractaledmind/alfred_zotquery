#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
from dependencies.pyzotero import zotero

"""
This script exports a Markdown formatted, APA-style reference (i.e. Author Date) of the selected item.
"""

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Get the item key from the system input
item_key = alp.args()[0]
#item_key = '6DEIA36D'

# Return an HTML formatted reference in APA style
ref = zot.item(item_key, content='citation', style='chicago-author-date')

# Remove the <span>...</span> tags
clean_ref = ref[0][6:-7].encode('utf-8')

# Change from (Author Date) to Author (Date)
result = re.sub(r"\((.*?)\s(.*?)\)", "\\1 (\\2)", clean_ref)

# Pass the reference to output
print result
			