#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import re
from dependencies.pyzotero import zotero
from dependencies import applescript

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# 35 item types
all_types = [u'artwork', u'audioRecording', u'bill', u'blogPost', u'book', u'bookSection', u'case', u'computerProgram', u'conferencePaper', u'dictionaryEntry', u'document', u'email', u'encyclopediaArticle', u'film', u'forumPost', u'hearing', u'instantMessage', u'interview', u'journalArticle', u'letter', u'magazineArticle', u'manuscript', u'map', u'newspaperArticle', u'note', u'patent', u'podcast', u'presentation', u'radioBroadcast', u'report', u'statute', u'tvBroadcast', u'thesis', u'videoRecording', u'webpage']
# 6 most common types
basic_types = [u'book', u'bookSection', u'conferencePaper', u'document', u'journalArticle', u'thesis']

# Prepare as Applescript List
basic_l = ['"' + x + '"' for x in basic_types]
basic_l = ', '.join(basic_l)
basic_l = '{' + basic_l + '}'

# Prepare as Applescript List
l = ['"' + x + '"' for x in all_types]
l = ', '.join(l)
l = '{' + l + '}'

# Prepare path to ZotQuery icon
icon_path = re.sub('/', ':', alp.local(join='icon.png'))

a_script = """
	set icon_ to "Macintosh HD{0}" as alias
	display dialog "Choose the Item Type for the current PDF" with title "ZotQuery Add Item" with icon icon_
	choose from list {1} with prompt "Which item type is the PDF?" with title "ZotQuery Add Item" default items item 1 of {1} OK button name "Choose" cancel button name "Not here"
	set res to result
	if res is false then
		choose from list {2} with prompt "Which item type is the PDF?" with title "ZotQuery Add Item" default items item 1 of {2} OK button name "Choose"
		set res to result
	end if
	return res
	""".format(icon_path, basic_l, l)
res = applescript.asrun(a_script)

# Get dictionary template for chosen item type
template = zot.item_template(str(res[0:-1]))


