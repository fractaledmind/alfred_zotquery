#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp
import sqlite3
import sys
import os

"""
This script queries your Zotero collections for any matches of the input query.
""" 

clone_database = os.path.join(alp.cache(), "zotquery.sqlite")
conn = sqlite3.connect(clone_database)
cur = conn.cursor()	
# Retrieve collection data from Zotero database
collection_query = """
		select collections.collectionName, collections.key
		from collections
		"""
coll_data = cur.execute(collection_query).fetchall()

query = sys.argv[1]
#query = 'epi'

xml_res = []
for i, item in enumerate(coll_data):
	
	if query.lower() in item[0].lower():
		
		res_dict = {'title': item[0], 'subtitle': 'Collection', 'valid': True, 'arg': 'c:' + item[1], 'icon': 'icons/n_collection.png'}
		res_item = alp.Item(**res_dict)
		xml_res.append(res_item)

conn.close()

alp.feedback(xml_res)