#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import alp
import json
from _zotquery import zot_string, info_format, prepare_feedback
from dependencies import applescript

"""
This script queries the JSON cache of your Zotero database for any matches of the query.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	# Get Zotero data from JSON cache
	with open(alp.storage(join='zotero_db.json'), 'r') as f:
		zot_data = json.load(f)
		f.close()

	# Get the user input
	query = alp.args()[0]
	#query = 'test'

	if len(query) <= 3:
		res_dict = {'title': 'Error', 'subtitle': "Need at least 4 letters to execute search", 'valid': False, 'uid': None, 'icon': 'icons/n_delay.png'}
		res_item = alp.Item(**res_dict)
		alp.feedback(res_item)
	else:
		# Search the Zotero data for matches
		results = alp.fuzzy_search(query, zot_data, key=lambda x: zot_string(x))

		# Clean up any duplicate results
		if not results == []:
			clean = []
			l = []
			for item in results:
				if item['id'] not in l:
					clean.append(item)
					l.append(item['id'])

			xml_res = prepare_feedback(clean)
					
			alp.feedback(xml_res)

		else:
			alp.feedback(alp.Item(**{'title': "Error", 'subtitle': "No results found.", 'valid': False, 'icon': 'icons/n_error.png'}))

# Not configured
else:
	a_script = """
			tell application "Alfred 2" to search "z:config"
			"""
	applescript.asrun(a_script)
