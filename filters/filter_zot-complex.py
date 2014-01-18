#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import json
from _zotquery import zotquery, zot_string, prepare_feedback

"""
This script queries the JSON cache of your Zotero database for matches of the query 
within the specified field, either Author or Title.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):
	# Get Zotero data from JSON cache
	with open(alp.storage(join='zotero_db.json'), 'r') as f:
		zot_data = json.load(f)
		f.close()

	# prepare specific query list: [key, value]
	query = [alp.args()[1], alp.args()[0]]
	#query = ['family', 'griff']

	if len(query[1]) <= 3:
		res_dict = {'title': 'Error', 'subtitle': "Need at least 4 letters to execute search", 'valid': False, 'uid': None, 'icon': 'icons/n_delay.png'}
		res_item = alp.Item(**res_dict)
		alp.feedback(res_item)
	else:
		# Search the Zotero data for matches
		res = zotquery(query, zot_data, sort='author')

		if res != []:
			# Rank the results
			results = alp.fuzzy_search(query[1], res, key=lambda x: zot_string(x))

			alp_res = prepare_feedback(results)

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