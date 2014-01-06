#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import alp
import json

# Get Zotero data from JSON cache
cache = alp.cache(join='zotero_db.json')
json_data = open(cache, 'r')
zot_data = json.loads(cache)
json_data.close()


# Types: [u'chapter', u'article-journal', u'book', u'paper-conference', u'thesis', u'personal_communication']

# Keys: [u'collection-title', u'DOI', u'ISBN', u'abstract', u'edition', u'title', u'ISSN', u'note', u'source', u'event-place', u'number-of-volumes', u'journalAbbreviation', u'issue', u'URL', u'call-number', u'volume', u'collection-number', u'date', u'publisher', u'shortTitle', u'language', u'number-of-pages', u'container-title', u'accessed', u'page']

##########
"""
+ BOOK (book, manuscript, or thesis):

	[Last, First]. [YYYY]. *[Title]*. [Pub. Loc.]: [Publisher].

+ ARTICLE (article-journal, article-magazine, article-newspaper, or paper-conference):

	[Last, First]. [YYYY]. "[Title]." *[Journal]* [Vol.]: [Pages].
	[Last, First]. [YYYY]. "[Title]." *[Journal]* [Vol.].[Iss.]: [Pages].

+ BOOK CHAPTER (chapter, entry-encyclopedia, or entry-dictionary):

	[Last, First]. [YYYY]. "[Title]." In *[Book Title]*, edited by [Editors]. [Pages]. [Pub. Loc.]: [Publisher].
	[Last, First]. [YYYY]. "[Title]." In *[Book Title]*. [Pages]. [Pub. Loc.]: [Publisher].
"""


# Create CiteKey
"""
for x in zot_data:
	# get id
	try:
		id = x['id']
	except KeyError:
		id = 'xx'
	# get first creator's last name	
	try:
		n = x['creator'][0]['family']
	except KeyError:
		n = 'xxx'
	# get year	
	try:
		y = x['data']['date']
	except KeyError:
		y = 'xxxx'
		
	print n + '_' + y + '_' + str(id)
"""	


for x in zot_data:
	
	## Format creator string // for all types
	############
	cr_l = set([item['type'] for item in x['creators']])
	# 1) len 1 = all same
	# 2) len 2 = one author, one editor
	# 3) len 3 = author, editor, translator

	for i, item in enumerate(x['creators']):
		# if all creators are same type
		if len(cr_l) == 1:
			
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

		
		if len(cr_l) == 2:
			None
				
	### Format date string // for all types
	try:
		date_final = x['data']['date'] + '.'
	except KeyError:
		date_final = 'xxx.'


	########
	### Special formatting for specific types
	
	## If ARTICLE type
	if x['type'] in ['article-journal', 'article-magazine', 'article-newspaper', 'paper-conference']:
		
		# Format title string 
		try:
			t = x['data']['title']
			ti = re.sub(r"\"(.*?)\"", "'\\1'", t)
			if not ti[-1] in ('.', '?', '!'):
				title_final = '\"' + ti + '.\"'
			else:
				title_final = '\"' + ti + '\"'
		except KeyError:
			title_final = '\"xxx.\"'
				
		# Format journal string
		try:
			journal_final = '*' + x['data']['container-title'] + '*'
		except KeyError:
			try:
				journal_final = '*' + x['collection-title'] + '*'
			except KeyError:
				journal_final = '*xxx*'

		# Format publication info string
		try:
			vol = x['data']['volume']
		except KeyError:
			vol = 'xxx'

		try:
			if type(x['data']['page']) == int:
				page = str(x['data']['page'])
			else:
				page = x['data']['page']
			if 'p' in page:
				page = page.split(' ')[1]
			page = re.sub(r"(\d*)(-|–|--|–)(\d*)", "\\1-\\3", page)
		except KeyError:
			page = 'xxx'

		try:
			iss = x['data']['issue']
			info_final = str(vol) + '.' + str(iss) + ': ' + page + '.'
		except KeyError:
			info_final = str(vol) + ': ' + page + '.'

		citation_final = creator_final + ' ' + date_final + ' ' + title_final + ' ' + journal_final + ' ' + info_final
		

	## If BOOK type	
	elif x['type'] in ['book', 'manuscript', 'thesis']:
		
		# Format title string // for all types
		try:
			t = x['data']['title']
			ti = re.sub(r"\"(.*?)\"", "'\\1'", t)
			if not ti[-1] in ('.', '?', '!'):
				title_final = '*' + ti + '.*'
			else:
				title_final = '*' + ti + '*'
		except KeyError:
			title_final = '*xxx.*'
		
		# Format publication location info string
		try:
			loc = x['data']['event-place']
		except KeyError:
			loc = 'xxx'
			
		# Format publisher info string
		try:
			pub = x['data']['publisher']
		except KeyError:
			pub = 'xxx'
			
		# Format publisher info string
		try:
			series = x['data']['collection-title']
			try:
				vol = str(x['data']['volume'])
				pub_final = series + ' ' + vol + '. ' + loc + ': ' + pub
			except KeyError:
				pub_final = series + '. ' + loc + ': ' + pub
		except KeyError:
			pub_final = loc + ': ' + pub
			
		citation_final = creator_final + ' ' + date_final + ' ' + title_final + ' ' + pub_final 
		if not citation_final[-1] == '.':
			citation_final = citation_final + '.'
		print citation_final
		print '\n'
		
	## If CHAPTER type
	# Keys for Chapters: [u'publisher', u'note', u'ISBN', u'language', u'shortTitle', u'title', u'URL', u'abstract', u'volume', u'event-place', u'source', u'date', u'accessed', u'collection-title', u'page']	
	
	# [Last, First]. [YYYY]. "[Title]." In *[Book Title]*, edited by [Editors]. [Pages]. [Pub. Loc.]: [Publisher].
	# [Last, First]. [YYYY]. "[Title]." In *[Book Title]*. [Pages]. [Pub. Loc.]: [Publisher].
	elif x['type'] in ['chapter', 'entry-encyclopedia', 'entry-dictionary']:
		
		# Format book title
		try:
			bk = x['data']['collection-title']
			book = 'In *' + bk + '*'
		except KeyError:
			book = '*xxx*'
					
		# Format publication location info string
		try:
			loc = x['data']['event-place']
		except KeyError:
			loc = 'xxx'
			
		# Format publisher info string
		try:
			pub = x['data']['publisher']
		except KeyError:
			pub = 'xxx'
			
		pub_final = loc + ': ' + pub

		
		citation_final = creator_final + ' ' + date_final + ' ' + title_final + ' '  
	else:
		None

				

	 
 