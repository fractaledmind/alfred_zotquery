#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import sqlite3

"""
This script queries your Zotero collections for any matches of the input query.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	# Connect to cloned .sqlite database
	conn = sqlite3.connect(alp.storage(join="zotquery.sqlite"))
	cur = conn.cursor()	

	# Retrieve collection data from Zotero database
	collection_query = """
			select collections.collectionName, collections.key
			from collections
			"""
	coll_data = cur.execute(collection_query).fetchall()
	conn.close()

	# Get user input
	query = alp.args()[0]
	#query = 'epic'

	if len(query) <= 2:
		res_dict = {'title': 'Error', 'subtitle': "Need at least 3 letters to execute search", 'valid': False, 'uid': None, 'icon': 'icons/n_delay.png'}
		res_item = alp.Item(**res_dict)
		alp.feedback(res_item)
	else:
		alp_res = []
		for item in coll_data:
			if query.lower() in item[0].lower():
				res_dict = {'title': item[0], 'subtitle': 'Collection', 'valid': True, 'arg': 'c:' + item[1], 'icon': 'icons/n_collection.png'}
				res_item = alp.Item(**res_dict)
				alp_res.append(res_item)

		if alp_res != []:
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