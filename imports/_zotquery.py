#!/usr/bin/python
# encoding: utf-8

########################
# Basic Helper methods
########################
def to_unicode(obj, encoding='utf-8'):
	"""Detects if object is a string and if so converts to unicode"""
	# from https://github.com/kumar303/unicode-in-python/blob/master/unicode.txt
	if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	return obj


def unidecode(str):
	from dependencies import unidecode
	return unidecode.unidecode(str)


def get_clipboard(): 
	from dependencies import applescript as a
	scpt = """
		return the clipboard
	"""
	data = a.asrun(scpt).strip()
	data = to_unicode(data)
	return data

	
def set_clipboard(data): 
	from dependencies import applescript as a
	uni = to_unicode(data)
	scpt = """
		set the clipboard to {0}
	""".format(a.asquote(uni.encode('utf-8')))
	a.asrun(scpt)
	
	
def get_path(type):	
	"""Read the paths JSON from non-volatile storage"""
	from workflow import Workflow
	import json
	wf = Workflow()
	with open(wf.datafile(u"paths.json"),'r') as f:
		path_d = json.load(f)
		f.close()
	return to_unicode(path_d[type])

def get_profile(path):
	"""Read the Zotero/Firefox profiles file"""
	import re
	import os.path
	prof = path + 'profiles.ini'
	if os.path.exists(prof):
		with open(prof,'r') as f:
			data = f.read()
			f.close()
		# Find the Profile sub-directory
		prof = re.search(r"(?<=^Path=)(.*?)$", data, re.M).group()
		prof_path = path + prof
		return to_unicode(prof_path)
	else:
		return u'None'
		
def check_cache():
	"""Does the cache need to be updated?"""
	from workflow import Workflow
	import os
	wf = Workflow()
	update = False
	spot = None
	### Step One: Check if cloned .sqlite database is up-to-date with Zotero database
	zotero_mod = os.stat(get_path(u'database_path'))[8]
	clone_mod = os.stat(wf.datafile(u'zotquery.sqlite'))[8]
	if zotero_mod > clone_mod:
		update = True
		spot = u"Clone"
	# Step Two: Check if JSON cache is up-to-date with the cloned database
	cache_mod = os.stat(wf.datafile(u'zotero_db.json'))[8]
	if (cache_mod - clone_mod) > 10:
		update = True
		spot = u"JSON"
	return [update, spot]
		


###########################
# Query and Result methods
###########################

def zot_string(d, scope='general', unicode_strict=True):
	"""Convert key values of item into string for fuzzy filtering"""
	def get_datum(d, key, val):
		l = []
		try:
			l = [d[key][val]]
		except KeyError:
			pass
		except TypeError:
			l = [x[val] for x in d[key]]	
		return l

	l = []
	if scope == 'general': 
		l += get_datum(d, 'data', 'title')
		l += get_datum(d, 'creators', 'family')
		l += get_datum(d, 'data', 'collection-title')
		l += get_datum(d, 'data', 'container-title')
		l += get_datum(d, 'name', 'zot-collections')
		l += get_datum(d, 'name', 'zot-tags')
		l += d['notes']
	elif scope == 'titles':
		l += get_datum(d, 'data', 'title')
		l += get_datum(d, 'data', 'collection-title')
		l += get_datum(d, 'data', 'container-title')
	elif scope == 'creators':
		l += get_datum(d, 'creators', 'family')
	elif scope == 'notes':
		l += d['notes']
	elif scope == 'in-collection':
		l += get_datum(d, 'name', 'zot-collections')
	elif scope == 'in-tag':
		l += get_datum(d, 'name', 'zot-tags')
	elif scope == 'attachments':
		l += get_datum(d, 'name', 'attachments')
	
	string = ' '.join(l)
	uni = to_unicode(string)
	if unicode_strict == True:
		return uni
	else:
		return unidecode(uni)


###
def prepare_feedback(results):
	"""Prepare dictionary for workflow results"""

	xml_res = []
	ids = []
	for item in results:
		if item['key'] not in ids:
			ids.append(item['key'])
			# Format the Zotero match results
			info = info_format(item)
			# Prepare data for Alfred
			title = item['data']['title']
			sub = info[0] + ' ' + info[1]
			# Create dictionary of necessary Alred result info.
			# For Alfred to remember results, add 'uid': str(item['id']), to dict
			res_dict = {'title': title, 'subtitle': sub, 'valid': True, 'arg': str(item['key'])}
			
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
					
			xml_res.append(res_dict)
	return xml_res			


def info_format(x):
	"""Format key information for item subtitle"""
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

	# TODO: ADD FORMATTING FOR OTHER CREATOR TYPES

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


def scan_cites(zot_data, item_key, uid):
	"""Exports ODT-RTF styled Scannable Cite"""
	
	for item in zot_data:
			if item['key'] == item_key:
				# Get YEAR var
				year = item['data']['issued']

				# Get and format CREATOR var
				if len(item['creators']) == 1:
					last = item['creators'][0]['family']
				elif len(item['creators']) == 2:
					last1 = item['creators'][0]['family']
					last2 = item['creators'][1]['family']
					last = last1 + ', & ' + last2
				elif len(item['creators']) > 2:
					for i in item['creators']:
						if i['type'] == 'author':
							last = i['family'] + ', et al.'
					try:
						last
					except:
						last = item['creators'][0]['family'] + ', et al.'

	prefix = ''
	suffix = ''

	scannable_cite = '{' + prefix + ' | ' + last + ', ' + year + ' | | ' + suffix + '|zu:' + uid + ':' + item_key + '}'

	return to_unicode(scannable_cite)
	#return scannable_cite.encode('utf-8')