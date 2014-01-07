#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp
import json
import sys
from _zotquery import zotquery, info_format

"""
This script queries the JSON cache of your Zotero database for any matches of the query.
""" 

# Get Zotero data from JSON cache
cache = alp.cache(join='zotero_db.json')
json_data = open(cache, 'r')
zot_data = json.load(json_data)
json_data.close()

# Get the user input
query = sys.argv[1]
#query = 'thomas'

try:
	# Search the Zotero data for matches
	results = zotquery(query, zot_data, sort='author')
# On a failure	
except:
	alp.log("Query failed.")
	iDict = dict(title="Error", subtitle="Query failed.", valid=True)
	i = alp.Item(**iDict)
	alp.feedback(i)

xml_res = []
for item in results:
	# Format the Zotero match results
	info = info_format(item)
	
	# Prepare data for Alfred
	title = item['data']['title']
	sub = info[0] + ' ' + info[1]
	
	res_dict = {'title': title, 'subtitle': sub, 'valid': True, 'uid': str(item['id']), 'arg': str(item['key'])}
	# Export items to Alfred xml with appropriate icons
	if item['type'] == 'article-journal':
		res_dict.update({'icon': 'icons/n_article.png'})
	elif item['type'] == 'book':
		res_dict.update({'icon': 'icons/n_book.png'})
	elif item['type'] == 'chapter':
		res_dict.update({'icon': 'icons/n_chapter.png'})
	elif item['type'] == 'paper-conference':
		res_dict.update({'icon': 'icons/n_conference.png'})
	else:
		res_dict.update({'icon': 'icons/n_written.png'})

	res_item = alp.Item(**res_dict)
	xml_res.append(res_item)
		
alp.feedback(xml_res)


