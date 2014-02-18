#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import re
import json
from pyzotero import zotero

with open(alp.cache(join='temp_attach_path.txt'), 'r') as f:
	data = json.load(f)
	f.close()

path = data['path']
title = path.rsplit('/', 1)[-1]
#print data['path']
key = alp.args()[0]

# Get the Library ID and API Key from the settings file
with open(alp.storage(join="settings.json"), 'r') as f:
	data = json.load(f)
	f.close()

# Initiate the call to the Zotero API
zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

# Try to attach PDF to item
if zot.attachment_simple([path], key) == True:
	print "Now refesh Zotero and update cache."
else:
	print ""
