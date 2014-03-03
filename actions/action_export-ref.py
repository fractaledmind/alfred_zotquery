#!/usr/bin/python
# encoding: utf-8
import sys
from workflow import Workflow

def main(wf):
	import json
	from pyzotero import zotero
	"""
	This script copies to the clipboard a reference to the selected item in the preferred style and format.
	"""

	# Get the Library ID and API Key from the settings file
	with open(wf.datafile(u"settings.json"), 'r') as f:
		data = json.load(f)
		f.close()
	# Get the user's export preferences
	with open(wf.datafile(u"prefs.json"), 'r') as f:
		prefs = json.load(f)
		f.close()

	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	# Get the item key from the system input
	item_key = wf.args[0]
	#item_key = 'NKT78PX8'

	# Return an HTML formatted citation in preferred style
	ref = zot.item(item_key, content='citation', style=prefs['csl'])
	# Remove the <span>...</span> tags
	clean_ref = ref[0][6:-7]

	# Export in chosen format
	if prefs['format'] == 'Markdown':
		from dependencies import html2md
		from _zotquery import set_clipboard

		# Convert the HTML to Markdown
		citation = html2md.html2text(clean_ref)

		if prefs['csl'] == 'bibtex':
			citation = '[@' + citation + ']'

		# Pass the Markdown citation to clipboard
		set_clipboard(citation.strip())

		print "Markdown"

	elif prefs['format'] == 'Rich Text':
		from dependencies import applescript

		if prefs['csl'] == 'bibtex':
			clean_ref = '[@' + clean_ref + ']'
			
		# Write html to temporary file
		with open(wf.cachefile(u"temp.html"), 'w') as f:
			f.write(clean_ref.encode('ascii', 'xmlcharrefreplace'))
			f.close

		# Convert html to RTF and copy to clipboard
		a_script = """
			do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
			""".format(wf.cachefile(u"temp.html"))
		applescript.asrun(a_script)

		print "Rich Text"


if __name__ == '__main__':
	wf = Workflow()
	sys.exit(wf.run(main))

   