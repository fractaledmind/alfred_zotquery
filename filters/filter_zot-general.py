#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import sys
from _zotquery import zot_string, info_format

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
#query = 'griff'

try:
	# Search the Zotero data for matches
	results = alp.fuzzy_search(query, zot_data, key=lambda x: zot_string(x))
# On a failure	
except:
	alp.log("Error! Query failed.")
	iDict = dict(title="Error!", subtitle="Query failed.", valid=True)
	i = alp.Item(**iDict)
	alp.feedback(i)


xml_res = []
for item in results:
	# Format the Zotero match results
	info = info_format(item)
	
	# Prepare data for Alfred
	title = item['data']['title']
	sub = info[0] + ' ' + info[1]

	# Create dictionary of necessary Alred result info.
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

	# If item has an attachment
	if item['attachments'] != []:
		res_dict.update({'subtitle': sub + ' Attachments: ' + str(len(item['attachments']))})
		res_dict.update({'icon': 'icons/n_attached.png'})

	res_item = alp.Item(**res_dict)
	xml_res.append(res_item)
		
alp.feedback(xml_res)
