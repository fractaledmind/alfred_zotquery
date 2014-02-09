#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import json
from _zotquery import setClipboardData

"""
This script reads, formats, outputs, and restarts the cached bibliography file.
"""

# Get the user's export preferences
with open(alp.storage(join="prefs.json"), 'r') as f:
	prefs = json.load(f)
	f.close()

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	# Export in chosen format
	if prefs['format'] == 'Markdown':
		with open(alp.cache(join='temp_bibliography.txt'), 'r') as f:
			data = f.read()
			f.close()

		# Convert the string to a list of citations
		l = data.split('\n\n')
		# Sort that list alphabetically
		sorted_l = sorted(l)

		# Begin with WORKS CITED
		if sorted_l[0] == '':
			sorted_l[0] = 'WORKS CITED'
		else:
			sorted_l.insert(0, 'WORKS CITED')

		# Pass the Markdown bibliography to clipboard
		setClipboardData('\n\n'.join(sorted_l))

		print "Markdown"

		# Restart the bibliography file
		with open(alp.cache(join='temp_bibliography.txt'), 'w') as f:
			f.write('')
			f.close()

	if prefs['format'] == 'Rich Text':

		# Read html from temporary bib file
		with open(alp.cache(join="temp_bibliography.html"), 'r') as f:
			data = f.read()
			f.close()

		# Convert the string to a list of citations
		l = data.split('<br>')
		# Sort that list alphabetically
		sorted_l = sorted(l)
		
		# Begin with WORKS CITED
		if sorted_l[0] == '':
			sorted_l[0] = 'WORKS CITED<br>'
		else:
			sorted_l.insert(0, 'WORKS CITED<br>')

		html_string = '<br><br>'.join(sorted_l)

		# Write html to temporary bib file
		with open(alp.cache(join="temp_bibliography.html"), 'w') as f:
			f.write(html_string)
			f.close()

		# Convert html to RTF and copy to clipboard
		a_script = """
			do shell script "textutil -convert rtf " & quoted form of "%s" & " -stdout | pbcopy"
			""" % alp.cache(join="temp_bibliography.html")
		applescript.asrun(a_script)

		# Write blank file to bib file
		with open(alp.cache(join="temp_bibliography.html"), 'w') as f:
			f.write('')
			f.close()

		print "Rich Text"

# Not configured
else:
	a_script = """
			tell application "Alfred 2" to search "z:config"
			"""
	applescript.asrun(a_script)