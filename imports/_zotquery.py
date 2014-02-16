#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import os
import re
import subprocess

###
def to_unicode(obj, encoding='utf-8'):
	"""Detects if object is a string and if so converts to unicode, if not already."""
	# from https://github.com/kumar303/unicode-in-python/blob/master/unicode.txt
	if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	return obj

###
def getClipboardData(): 
  	p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE) 
	retcode = p.wait() 
	data = p.stdout.read() 
	return data 
	
def setClipboardData(data): 
	p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE) 
	p.stdin.write(data.encode('utf-8')) 
	p.stdin.close() 
	retcode = p.wait()
	
###
def get_path(type):	
	"""Read the paths JSON from non-volatile storage"""
	with open(alp.storage(join="paths.json"),'r') as f:
		path_d = json.load(f)
		f.close()
	return path_d[type]
	
###
def zot_string(d):
	"""Convert key values of item into string for fuzzy ranking"""
	string = ''
	for key, val in d.items():
		if key == 'data':
			for sub_key, sub_val in val.items():
				if sub_key in ['title', 'container-title', 'collection-title']:
					string += ' ' + sub_val
									
		# Since the creator key contains a list
		elif key == 'creators':
			for i in val:
				for key1, val1 in i.items():
					if key1 == 'family':
						string += ' ' + val1

	return string

###
def get_profile(path):
    """Read the profiles file"""
    prof = path + 'profiles.ini'
    if os.path.exists(prof):
        file = open(prof, 'r')
        data = file.read()
        file.close()
        # Find the Profile sub-directory
        prof = re.search(r"(?<=^Path=)(.*?)$", data, re.M).group()
        prof_path = path + prof
        return prof_path
    else:
        return 'None'
		
###
def check_cache():
	"""Does the cache need to be updated?"""
	update = False

	### Step One: Check if cloned .sqlite database is up-to-date with Zotero database
	zotero_mod = os.stat(get_path('database_path'))[8]
	clone_mod = os.stat(alp.storage(join='zotquery.sqlite'))[8]

	if zotero_mod > clone_mod:
		update = True
		alp.log("Cloned db needs to be updated")

	# Step Two: Check if JSON cache is up-to-date with the cloned database
	cache_mod = os.stat(alp.storage(join='zotero_db.json'))[8]
	if (cache_mod - clone_mod) > 10:
		update = True
		alp.log("Cache needs to be updated")
	return update
		
###		
def zotquery(query, zot_data, sort='none'):
	"""Query Zotero for Alfred argument."""
	
	# Query can either be generic (does any key's value contain query) or specific (does this key's value contain query).
	# If generic, query should be a simple string.
	# If specific, query should be a list, [key, search]
	
	matches = []
	for i, item in enumerate(zot_data):
		# if query is generic/simple
		if type(query) is str:
			for key, val in item.items():
				if key == 'data':
					for sub_key, sub_val in val.items():
						if sub_key in ['title', 'container-title', 'collection-title']:
							if query.lower() in sub_val.lower():
								if sort == 'title':
									matches.insert(0, item)
								else:
									matches.append(item)
						elif not type(sub_val) == int:
							if query.lower() in sub_val.lower():
								matches.append(item)
							
				# Since the creator key contains a list
				elif key == 'creators':
					for i in val:
						for key1, val1 in i.items():
							if query.lower() in val1.lower():
								if sort == 'author':
									matches.insert(0, item)
								else:
									matches.append(item)
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

		# if query is specific/complex
		elif type(query) is list:
			[search_key, search_val] = [query[0], query[1]]
			
			for key, val in item.items():	
				if key == 'creators':
					for i in val:
						for sub_key, sub_val in i.items():
							if sub_key.lower() == search_key.lower():
								if search_val.lower() in sub_val.lower():
									matches.append(item)
				elif key == 'data':
					for sub_key, sub_val in val.items():
						if sub_key.lower() == search_key.lower():
							if search_val.lower() in sub_val.lower():
								matches.append(item)
	
	# Clean up any duplicate results
	if not matches == []:
		clean = []
		l = []
		for item in matches:
			if item['id'] not in l:
				clean.append(item)
				l.append(item['id'])
		return clean
	else:
		return matches


###
def info_format(x):
	# Format creator string // for all types
	for i, item in enumerate(x['creators']):
		if not item['family'] == '':
			last = item['family']
		else:
			last = 'xxx'
		if not item['given'] == '':
			first = item['given']
		else: 
			first = 'xxx'
			
		## if author (or anything else)
		if item['type'] == 'editor':
			suffix_sg = ', ed.'
			suffix_pl = ', eds.'
		elif item['type'] == 'translator':
			suffix_sg = ', trans.'
			suffix_pl = ', trans.'
		else:
			suffix_sg = ''
			suffix_pl = ''
			
		# if single creator
		if len(x['creators']) == 1:
			creator_ref = last + suffix_sg
			creator_final = last + ', ' + first + suffix_sg

		# if two or more creators
		elif len(x['creators']) > 1:
			if i == 0:
				one = last + ', ' + first
				one_ref = last
			elif i == 1:
				two = first + ' ' + last
				two_ref = last
				
				# if only 2 creators
				if len(x['creators']) == 2:
					creator_ref = one_ref + ' and ' + two_ref + suffix_pl
					creator_final = one + ' and ' + two + suffix_pl
					
				# if more than 2 creators
				elif len(x['creators']) > 2:
					creator_ref = one_ref + ' and ' + two_ref + ' et al.' + suffix_pl
					creator_final = one + ' and ' + two + ' et al.' + suffix_pl
		
	if not creator_final[-1] in ['.', '!', '?']:
		creator_final = creator_final + '.'


	# ADD FORMATTING FOR OTHER CREATOR TYPES

	# Format date string // for all types
	try:
		date_final = x['data']['issued'] + '.'
	except KeyError:
		date_final = 'xxx.'

	# Format title string // for all types
	try:
		x['data']['title']
		# Check title for ending punctuation
		if not x['data']['title'][-1] == ('.' or '?' or '!'):
			title_final = '\"' + x['data']['title'] + '.\"'
		else:
			title_final = '\"' + x['data']['title'] + '\"'
	except KeyError:
		title_final = '\"xxx.\"'

	return [creator_ref, date_final, title_final]

###
def prepare_feedback(results):
	xml_res = []
	for item in results:
		# Format the Zotero match results
		info = info_format(item)
		
		# Prepare data for Alfred
		title = item['data']['title']
		sub = info[0] + ' ' + info[1]
		
		# Create dictionary of necessary Alred result info.
		res_dict = {'title': title, 'subtitle': sub, 'valid': True, 'uid': str(item['id']), 'arg': str(item['key'])}
		
		# If item has an attachment
		if item['attachments'] != []:
			res_dict.update({'subtitle': sub + ' Attachments: ' + str(len(item['attachments']))})
		
		# Export items to Alfred xml with appropriate icons
		if item['type'] == 'article-journal':
			if item['attachments'] == []: 
				res_dict.update({'icon': 'icons/n_article.png'})
			else:
				res_dict.update({'icon': 'icons/att_article.png'})
		elif item['type'] == 'book':
			if item['attachments'] == []:
				res_dict.update({'icon': 'icons/n_book.png'})
			else:
				res_dict.update({'icon': 'icons/att_book.png'})
		elif item['type'] == 'chapter':
			if item['attachments'] == []:
				res_dict.update({'icon': 'icons/n_chapter.png'})
			else:
				res_dict.update({'icon': 'icons/att_book.png'})
		elif item['type'] == 'paper-conference':
			if item['attachments'] == []:
				res_dict.update({'icon': 'icons/n_conference.png'})
			else:
				res_dict.update({'icon': 'icons/att_conference.png'})
		else:
			if item['attachments'] == []:
				res_dict.update({'icon': 'icons/n_written.png'})
			else:
				res_dict.update({'icon': 'icons/att_written.png'})
				
		res_item = alp.Item(**res_dict)
		xml_res.append(res_item)
		
	return xml_res			