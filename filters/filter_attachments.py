#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import os.path
import json
from _zotquery import zot_string, prepare_feedback
from dependencies import applescript

"""
This script searches only within items that have attachments.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	# Get Zotero data from JSON cache
	with open(alp.storage(join='zotero_db.json'), 'r') as f:
		zot_data = json.load(f)
		f.close()

	query = alp.args()[0]
	#query = 'epistem'

	if len(query) <= 2:
		res_dict = {'title': 'Error', 'subtitle': "Need at least 3 letters to execute search", 'valid': False, 'uid': None, 'icon': 'icons/n_delay.png'}
		res_item = alp.Item(**res_dict)
		alp.feedback(res_item)
	else:
		matches = []
		for item in zot_data:
			if item['attachments'] != []:
			
				for key, val in item.items():
					if key == 'data':
						for sub_key, sub_val in val.items():
							if sub_key in ['title', 'container-title', 'collection-title']:
								if query.lower() in sub_val.lower():
									matches.insert(0, item)
								
					# Since the creator key contains a list
					elif key == 'creators':
						for i in val:
							for key1, val1 in i.items():
								if query.lower() in val1.lower():
									matches.insert(0, item)

					elif key ==  'zot-collections':
						for i in val:
							if query.lower() in i['name'].lower():
								matches.append(item)

					elif key == 'zot-tags':
						for i in val:
							if query.lower() in i['name'].lower():
								matches.append(item)

					elif key == 'notes':
						for i in val:
							if query.lower() in i.lower():
								matches.append(item)

		if matches != []:

			# Rank the results
			results = alp.fuzzy_search(query, matches, key=lambda x: zot_string(x))
				
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