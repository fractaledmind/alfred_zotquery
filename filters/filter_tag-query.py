#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp
import json
import sys
import re
from _zotquery import info_format

"""
This script searches within the tag chosen in the previous step (z:tag) for the queried term.
""" 

# Read the inputted Collection name to a temporary file
temp = alp.cache(join='tag_query_result.txt')
file = open(temp, 'r')
collection = file.read().decode('utf-8')
file.close()

# Remove the forward-slash space delimiters
result = re.sub(r"\\\s", " ", collection)

# Get Zotero data from JSON cache
cache = alp.cache(join='zotero_db.json')
json_data = open(cache, 'r')
zot_data = json.load(json_data)
json_data.close()

#query = sys.argv[1]
query = 'n'

matches = []
for i, item in enumerate(zot_data):
	for jtem in item['zot-tags']:
		if result == jtem['name']:
	
			for key, val in item.items():
				if key == 'data':
					for sub_key, sub_val in val.items():
						if sub_key in ['title', 'container-title', 'collection-title']:
							if query.lower() in sub_val.lower():
								matches.insert(0, item)
						elif sub_key in ['note', 'event-place', 'source', 'publisher', 'abstract']:
							if query.lower() in sub_val.lower():
								matches.append(item)
							
				# Since the creator key contains a list
				elif key == 'creator':
					for i in val:
						for key1, val1 in i.items():
							if query.lower() in val1.lower():
								matches.insert(0, item)

# Clean up any duplicate results
if not matches == []:
	clean = []
	l = []
	for item in matches:
		if item['id'] not in l:
			clean.append(item)
			l.append(item['id'])

	final = clean
else:
	final = matches
	
	
xml_res = []
for item in final:
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
