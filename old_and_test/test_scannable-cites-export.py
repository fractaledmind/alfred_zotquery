#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
from dependencies import applescript

"""
EXAMPLES:
{ | Morrison, 1956 | | |zu:1140739:FGBSNPS8}

{ | Jauss, et al., 1990 | | |zu:1140739:KI66IFPT}

{ | Wittern, & Pellegrin, 1996 | | |zu:1140739:JQHKJ4NZ}
"""

# Get Zotero data from JSON cache
with open(alp.storage(join='zotero_db.json'), 'r') as f:
	zot_data = json.load(f)
	f.close()

# Get the User ID from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()
uid = data['user_id']


item_key = alp.args()[0]
#item_key = 'KI66IFPT'

for item in zot_data:
	if item['key'] == item_key:
		year = item['data']['issued']

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


# See if user wishes to insert prefix
#icon_path = re.sub('/', ':', alp.local(join='icon.png'))
#a_script = """
#	set icon_ to "Macintosh HD%s" as alias
#	set prefix to display dialog "Insert prefix for citation?" default answer "" with title "ZotQuery Citation Export" with icon icon_
#	text returned of prefix
#""" % icon_path
#prefix = applescript.asrun(a_script)[0:-1]

# See if user wishes to insert suffix
#a_script = """
#	set icon_ to "Macintosh HD%s" as alias
#	set suffix to display dialog "Insert suffix for citation?" default answer "" with title "ZotQuery Citation Export" with icon icon_
#	text returned of suffix
#""" % icon_path
#suffix = applescript.asrun(a_script)[0:-1]

prefix = ''
suffix = ''

scannable_cite = '{' + prefix + ' | ' + last + ', ' + year + ' | | ' + suffix + '|zu:' + uid + ':' + item_key + '}'

print scannable_cite
