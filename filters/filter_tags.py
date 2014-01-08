#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp
import sqlite3
import sys
import os

"""
This script queries your Zotero tags for any matches of the input query.
""" 

clone_database = os.path.join(alp.cache(), "zotquery.sqlite")
conn = sqlite3.connect(clone_database)
cur = conn.cursor()	
# Retrieve collection data from Zotero database
tag_query = """
		select tags.name, tags.key
		from tags
		"""
tag_data = cur.execute(tag_query).fetchall()

query = sys.argv[1]
#query = 'sem'

xml_res = []
for i, item in enumerate(tag_data):
	
	if query.lower() in item[0].lower():
		
		res_dict = {'title': item[0], 'subtitle': 'Tag', 'valid': True, 'arg': 't:' + item[0], 'icon': 'icons/n_tag.png'}
		res_item = alp.Item(**res_dict)
		xml_res.append(res_item)

conn.close()

alp.feedback(xml_res)
