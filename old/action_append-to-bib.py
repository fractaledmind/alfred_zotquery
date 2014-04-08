#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow import Workflow

def main(wf):
	import json
	import re
	import os.path
	from pyzotero import zotero
	from zq_utils import to_unicode
	"""
	This script appends a citation to a temporary bibliography file 
	in the preferred style and format.
	"""

	# Get the Library ID and API Key from the settings file
	with open(wf.datafile(u"settings.json"), 'r') as f:
		data = json.load(f)
		f.close()
	# Get the user's export preferences
	with open(wf.datafile(u"prefs.json"), 'r') as f:
		prefs = json.load(f)
		f.close()

	# Create files, if necessary
	if not os.path.exists(wf.cachefile(u"temp_bibliography.html")):
		with open(wf.cachefile(u"temp_bibliography.html"), 'w') as f:
			f.write('')
			f.close()
	if not os.path.exists(wf.cachefile(u"temp_bibliography.txt")):
		with open(wf.cachefile(u"temp_bibliography.txt"), 'w') as f:
			f.write('')
			f.close()

	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	# Get the item key from the system input
	item_key = wf.args[0]

	# Return an HTML formatted citation in preferred style
	ref = zot.item(item_key, content='bib', style=prefs['csl'])

	uref = to_unicode(ref[0], encoding='utf-8')
	html_ref = uref.encode('ascii', 'xmlcharrefreplace')

	# Remove url, DOI, and "pp. ", if there
	if prefs['csl'] != 'bibtex':
		html_ref = re.sub("(?:http|doi)(.*?)$|pp. ", "", html_ref)

	# Export in chosen format
	if prefs['format'] == 'Markdown':
		from dependencies import html2md

		# Convert the HTML to Markdown
		citation = html2md.html2text(html_ref)
		# Replace "_..._" MD italics with "*...*"
		result = re.sub("_(.*?)_", "*\\1*", citation)

		# Append final, formatted input to biblio file
		with open(wf.cachefile(u"temp_bibliography.txt"), 'a') as f:
			f.write(result.strip())
			f.write('\n\n')
			f.close()
		print "Markdown"
		
	elif prefs['format'] == 'Rich Text':
		# Write html to temporary file
		with open(wf.cachefile(u"temp_bibliography.html"), 'a') as f:
			f.write(html_ref[23:])
			f.write('<br>')
			f.close
		print "Rich Text"

if __name__ == '__main__':
	wf = Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
	sys.exit(wf.run(main))

   