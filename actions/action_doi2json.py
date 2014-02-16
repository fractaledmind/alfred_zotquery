#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import re
import alp
import json
import _mappings

from dependencies.pyzotero import requests
from dependencies import applescript
from dependencies.pyzotero import zotero

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

doi = "10.1163/156852882x00096"
#doi = alp.args()[0]

# use REST API (see http://crosscite.org/cn/)
reftype = 'application/vnd.citationstyles.csl+json'

headers = {'Accept': reftype}
r = requests.post('http://dx.doi.org/' + doi, headers=headers,
                  allow_redirects=True)

doi_dict = {}
for key, val in r.json().items():
	if key == 'type': 
		type = val
		doi_dict.update({'itemType': val})
	else:
		zot_key = _mappings.trans_fields(key, 'zot')
		doi_dict.update({zot_key: val})
	

# Invalid keys present in item 1: editor author
# u'creators': [{u'lastName': u'', u'creatorType': u'author', u'firstName': u''}]
print doi_dict['date']['date-parts']


#template = zot.item_template(_mappings.trans_types(type, 'zot'))


"""
publisher = str
DOI = str
type = str
title = str
url = str
date = dict
author = list of dicts
volume = num/str
editor = list
publicationTitle = str
issue = num/str
pages = num/str

- - -

DOI
itemType
extra
seriesText
series
abstractNote
archive
attachments = list
title
ISSN
archiveLocation
journalAbbreviation
issue
seriesTitle
tags = []
accessDate
libraryCatalog
volume
callNumber
date
pages
shortTitle
language
rights
url
notes = list
publicationTitle
creators = list of dicts

- - -

{u'DOI': u'', u'itemType': u'journalArticle', u'extra': u'', u'seriesText': u'', u'series': u'', u'abstractNote': u'', u'archive': u'', u'attachments': [], u'title': u'', u'ISSN': u'', u'archiveLocation': u'', u'journalAbbreviation': u'', u'issue': u'', u'seriesTitle': u'', u'tags': [], u'accessDate': u'', u'libraryCatalog': u'', u'volume': u'', u'callNumber': u'', u'date': u'', u'pages': u'', u'shortTitle': u'', u'language': u'', u'rights': u'', u'url': u'', u'notes': [], u'publicationTitle': u'', u'creators': [{u'lastName': u'', u'creatorType': u'author', u'firstName': u''}]}
{u'publisher': u'Brill Academic Publishers', u'DOI': u'10.1163/156852882X00096', 'itemType': u'article-journal', u'title': u"Plato's Myths of Judgement", u'url': u'http://dx.doi.org/10.1163/156852882X00096', u'author': [{u'given': u'Julia', u'family': u'Annas'}], u'volume': u'27', None: u'article-journal', u'publicationTitle': u'Phronesis', u'editor': [], u'date': {u'date-parts': [[1982, 1, 1]]}, u'issue': u'1', u'pages': u'119-143'}
"""
