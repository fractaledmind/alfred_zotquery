#!/usr/bin/python
# encoding: utf-8
import sys
from workflow import Workflow

def main(wf):
	import json
	import os.path
	from pyzotero import zotero
	"""
	This script exports a Bibliography for the selected collection in the preferred style and format.
	"""

	_inp = wf.args[0].split(':')
	#_inp = 'c:GXWGBRJD'.split(':')

	# Get the Library ID and API Key from the settings file
	with open(wf.datafile(u"settings.json"), 'r') as f:
		data = json.load(f)
		f.close()
	# Get the user's export preferences
	with open(wf.datafile(u"prefs.json"), 'r') as f:
		prefs = json.load(f)
		f.close()

	# Create files, if necessary
	if not os.path.exists(wf.cachefile(u"full_bibliography.html")):
		with open(wf.cachefile(u"full_bibliography.html"), 'w') as f:
			f.write('')
			f.close()

	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	# If a Collection
	if _inp[0] == 'c':
		# Get the item key from the system input
		coll_key = _inp[1]
		
		# Return a list of HTML formatted citations in preferred style
		cites = zot.collection_items(coll_key, content='bib', style=prefs['csl'])
		
	elif _inp[0] == 't':
		# Get the item key from the system input
		tag_key = _inp[1]
		
		# Return a list of HTML formatted citations in preferred style
		try:
			cites = zot.tag_items(tag_key, content='bib', style=prefs['csl'])
		except:
			cites = ""

	# Export in chosen format
	if prefs['format'] == 'Markdown':
		import re
		from dependencies import html2md
		from _zotquery import set_clipboard

		md_cites = []
		for ref in cites:
			html_ref = ref.encode('ascii', 'xmlcharrefreplace')
			# Convert the HTML to Markdown
			citation = html2md.html2text(html_ref)

			# Remove url, DOI, and "pp. ", if there
			if prefs['csl'] != 'bibtex':
				citation = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
				# Replace "_..._" MD italics with "*...*"
				citation = re.sub("_(.*?)_", "*\\1*", citation)
			# Append the Markdown citation to a new list
			md_cites.append(citation)

		# Sort that list alphabetically
		sorted_md = sorted(md_cites)
		# Begin with WORKS CITED header
		sorted_md.insert(0, 'WORKS CITED\n')

		# Pass the Markdown bibliography to clipboard
		set_clipboard('\n'.join(sorted_md))

		print prefs['format']

	elif prefs['format'] == 'Rich Text':
		from dependencies import applescript
		import re

		# Write html to temporary bib file
		with open(wf.cachefile(u"full_bibliography.html"), 'w') as f:
			for ref in cites:
				f.write(ref.encode('ascii', 'xmlcharrefreplace'))
				f.write('<br>')
			f.close()

		# Read and clean-up html
		with open(wf.cachefile(u"full_bibliography.html"), 'r+') as f:
			bib_html = f.read()
			if prefs['csl'] != 'bibtex':
				bib_html = re.sub(r"http(.*?)\.(?=<)", "", bib_html)
				bib_html = re.sub(r"doi(.*?)\.(?=<)", "", bib_html)
			bib_html = re.sub("pp. ", "", bib_html)
			
			html_cites = bib_html.split('<br>')
			sorted_html = sorted(html_cites)
			sorted_html.insert(0, 'WORKS CITED<br>')
			final_html = '<br>'.join(sorted_html)
			f.write(final_html)
			f.close()

		# Convert html to RTF and copy to clipboard
		a_script = """
			do shell script "textutil -convert rtf " & quoted form of "%s" & " -stdout | pbcopy"
			""" % alp.cache(join="full_bibliography.html")
		applescript.asrun(a_script)

		# Write blank file to bib file
		with open(wf.cachefile(u"full_bibliography.html"), 'w') as f:
			f.write('')
			f.close()

		print prefs['format']

if __name__ == '__main__':
	wf = Workflow()
	sys.exit(wf.run(main))