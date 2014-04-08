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


def check_for_workflow(name):
	import os
	import plistlib

	workflows_dir = os.path.dirname(os.getcwd())
	all_wfs = os.walk(workflows_dir).next()[1]

	for wf in all_wfs:
		plist = workflows_dir + u"/" + wf + u"/info.plist"
		if os.path.isfile(plist):
			plist_info = plistlib.readPlist(plist)
			wf_name = plist_info['name'].lower()
			if wf_name == name.lower():
				found = True
				break
	try:
		found
		return True
	except:
		return False


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

def zot_string(d, scope='general'):
	"""Convert key values of item into string for fuzzy filtering"""
	def get_datum(d, key, val):
		try:
			return [d[key][val]]
		except KeyError:
			return []
		except TypeError:
			return [x[val] for x in d[key]]

	l = []
	if scope == 'general': 
		l += get_datum(d, 'data', 'title')
		l += get_datum(d, 'creators', 'family')
		l += get_datum(d, 'data', 'collection-title')
		l += get_datum(d, 'data', 'container-title')
		l += get_datum(d, 'data', 'issued')
		l += get_datum(d, 'name', 'zot-collections')
		l += get_datum(d, 'name', 'zot-tags')
		l += d['notes']
	elif scope == 'titles':
		l += get_datum(d, 'data', 'title')
		l += get_datum(d, 'data', 'collection-title')
		l += get_datum(d, 'data', 'container-title')
		l += get_datum(d, 'data', 'issued')
	elif scope == 'creators':
		l += get_datum(d, 'creators', 'family')
		l += get_datum(d, 'data', 'issued')
	elif scope == 'notes':
		l += d['notes']
	elif scope == 'in-collection':
		l += get_datum(d, 'name', 'zot-collections')
	elif scope == 'in-tag':
		l += get_datum(d, 'name', 'zot-tags')
	elif scope == 'attachments':
		l += get_datum(d, 'name', 'attachments')
	
	str = ' '.join(l)
	uni = to_unicode(str)
	return uni

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

			try:
				library_id = item['zot-collections'][0]['library_id']
			except:
				library_id = '0'
			_arg = str(library_id) + '_' + str(item['key'])

			# Create dictionary of necessary Alred result info.
			# For Alfred to remember results, add 'uid': str(item['id']), to dict
			res_dict = {'title': title, 'subtitle': sub, 'valid': True, 'arg': _arg}
			
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
	creator_list = []
	for item in x['creators']:
		last = item['family']

		## if author (or anything else)
		if item['type'] == 'editor':
			last = last + ' (ed.)'
		elif item['type'] == 'translator':
			last = last + ' (trans.)'
		creator_list.append(last)
	
	if len(x['creators']) == 1:
		creator_ref = ''.join(creator_list)
	elif len(x['creators']) == 2:
		creator_ref = ' and '.join(creator_list)
	elif len(x['creators']) > 2:
		creator_ref = ', '.join(creator_list[:-1])
		creator_ref = creator_ref + ', and ' + creator_list[-1]
	
	if not creator_ref[-1] in ['.', '!', '?']:
		creator_ref = creator_ref + '.'

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