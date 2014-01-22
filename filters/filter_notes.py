#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import json
from _zotquery import zot_string, prepare_feedback

"""
This script searches only within items' notes.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	# Get Zotero data from JSON cache
	with open(alp.storage(join='zotero_db.json'), 'r') as f:
		zot_data = json.load(f)
		f.close()

	query = alp.args()[0]
	#query = 'lateiner'

	# Search only within item notes
	matches = []
	for item in zot_data:
		if item['notes'] != []:
			for i in item['notes']:
				if query.lower() in i.lower():
					matches.append(item)

	if matches != []:
			
		alp_res = prepare_feedback(matches)

		# Remove any duplicate items
		xml_res = list(set([x for x in alp_res]))
				
		alp.feedback(xml_res)
	else:
		alp.feedback(alp.Item(**{'title': "Error", 'subtitle': "No results found.", 'valid': False, 'icon': 'icons/n_error.png'}))

# Not configured
else:
	a_script = """
		tell application "Alfred 2" to search "z:config"
		"""
	applescript.asrun(a_script)