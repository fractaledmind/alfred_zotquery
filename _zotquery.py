#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import json
import os
import alp
import os.path
import time
import sys
import re

###
def to_unicode(obj, encoding='utf-8'):
# Detects if object is a string and if so converts to unicode, if not already.
# from https://github.com/kumar303/unicode-in-python/blob/master/unicode.txt
	if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	return obj

###
def get_zotero_db():
	
	"""Find the user's Zotero sqlite database."""

	home = os.environ["HOME"]

	zf_path = home + "/Library/Application Support/Firefox/"

	if os.path.exists(zf_path + 'profiles.ini'):
		# Read the profiles file
		prof = zf_path + 'profiles.ini'
		file = open(prof, 'r')
		data = file.read()
		file.close()
		# Find the Profile sub-directory	
		prof = re.search(r"(?<=^Path=)(.*?)$", data, re.M).group()
		prof_path = zf_path + prof
		
		if os.path.exists(prof_path + '/prefs.js'):
			# Read the preferences file
			prefs = prof_path + '/prefs.js'
			file = open(prefs, 'r')
			pr_data = file.read()
			file.close()
			# Find the directory for Zotero data
			zot_path = re.search("(?<=^user_pref\\(\"extensions.zotero.dataDir\", \")(.*?)(?=\"\\);$)", pr_data, re.M).group()
			
			if os.path.exists(zot_path + '/zotero.sqlite'):
				db_path = zot_path + '/zotero.sqlite'
				return db_path
				alp.log("Found the user's Zotero database.")
			else:
				alp.log("Could not find Zotero sqlite database.")
				
		else:
			alp.log("Could not find Zotero's Firefox preferences.")

	else:
		zotero_path = home + '/Library/Application Support/Zotero/'
		# Check Zotero main folder exists
		if os.path.exists(zotero_path) == True:
			for root, dirs, files in os.walk(zotero_path):
				for file in files:
					if file.endswith('zotero.sqlite'):
						db_path = os.path.join(root, file)
			# Check if zotero.sqlite file is found	
			if 'db_path' in locals():
				return db_path
				# Log the results
				alp.log("Found the user's Zotero database.")
			else:
				alp.log("Could not find Zotero sqlite database.")
				
		else:
			for root, dirs, files in os.walk(home):
				for file in files:
					if file.endswith('zotero.sqlite'):
						db_path = os.path.join(root, file)
			# Check if zotero.sqlite file is found	
			if 'db_path' in locals():
				return db_path
				alp.log("Found the user's Zotero database.")
		
###
def check_cache():
	
	"""Check if user's Zotero sqlite database has been modified since last cache was created."""
	
	try:
		# Get the cache path and its modification date
		cache_path = alp.cache(join='zotero_db.json')
		cache_mod = time.ctime(os.path.getmtime(cache_path))
	except:
		alp.log("Zotero cache not found.")
		
	try:
		# Get the Zotero database path and its modification date
		zotero_path = getZoteroDB()
		zotero_mod = time.ctime(os.path.getmtime(zotero_path))
	except:
		alp.log("Backup Failed! Zotero database locked.")
				
	if zotero_mod > cache_mod:
		return False # Zotero is newer, so Cache needs to update
		alp.log("Cache needs to be updated")
	elif zotero_mod < cache_mod:
		return True # Cache is newer
		alp.log("Cache is up-to-date")
		
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
				elif key == 'type':
					if key.lower() == search_key.lower():
						if search_val.lower() in val.lower():
							matches.append(item)
				elif key == 'id':
					if key.lower() == search_key.lower():
						if search_val.lower() in str(val).lower():
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
	