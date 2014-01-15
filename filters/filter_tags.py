#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import sqlite3

"""
This script queries your Zotero tags for any matches of the input query.
""" 

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):
	# Connect to cloned .sqlite database
	conn = sqlite3.connect(alp.storage(join="zotquery.sqlite"))
	cur = conn.cursor()	

	# Retrieve collection data from Zotero database
	tag_query = """
			select tags.name, tags.key
			from tags
			"""
	tag_data = cur.execute(tag_query).fetchall()
	conn.close()

	# Get user input
	query = alp.args()[0]
	#query = 'sem'

	if len(query) <= 3:
		res_dict = {'title': 'Error', 'subtitle': "Need at least 4 letters to execute search", 'valid': False, 'uid': None, 'icon': 'icons/n_delay.png'}
		res_item = alp.Item(**res_dict)
		alp.feedback(res_item)
	else:
		xml_res = []
		for item in tag_data:	
			if item[0].lower().startswith(query.lower()):
				res_dict = {'title': item[0], 'subtitle': 'Tag', 'valid': True, 'arg': 't:' + item[0], 'icon': 'icons/n_tag.png'}
				res_item = alp.Item(**res_dict)
				xml_res.append(res_item)

		if xml_res != []:
			alp.feedback(xml_res)
		else:
			alp.feedback(alp.Item(**{'title': "Error", 'subtitle': "No results found.", 'valid': False, 'icon': 'icons/n_error.png'}))

# Not configured
else:
	a_script = """
			tell application "Alfred 2" to search "z:config"
			"""
	applescript.asrun(a_script)
	