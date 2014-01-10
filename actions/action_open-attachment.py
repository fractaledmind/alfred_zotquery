#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp, applescript
import sys
import json
import os.path
import subprocess

"""
This script opens the attachment for the chosen item, 
either in the default program for that file type, of if not found
in Zotero itself.
"""

# Get Zotero data from JSON cache
cache = alp.cache(join='zotero_db.json')
json_data = open(cache, 'r')
zot_data = json.load(json_data)
json_data.close()

query = sys.argv[1]
#query = 'KPQW3ZPT'

# Get the item's attachement path and attachment key
for item in zot_data:
	if query == item['key']:
		for jtem in item['attachments']:
			path = jtem['path']
			key = jtem['key']


if os.path.isfile(path):
    # Open file in default application
    subprocess.Popen(['open', path], shell=False, stdout=subprocess.PIPE)
else:
	# Open the attachment in Zotero
	a_script = """
	tell application id "org.zotero.zotero"
		activate
		activate
		open location "zotero://select/items/0_%s"
	end tell""" % key
	applescript.asrun(a_script)
