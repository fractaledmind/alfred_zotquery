#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow import Workflow

def main(wf):
	import json
	
	"""
	This script copies to the clipboard a reference to the selected item 
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

	# Get the item key from the system input
	item_key = wf.args[0]
	#item_key = 'FIQF74GD'


	# If user exports ODT-RTF Scannable Cites, don't use `pyzotero`
	if prefs['csl'] == 'odt-scannable-cites':
		from zq_utils import set_clipboard, scan_cites

		# Get current Zotero data from JSON cache
		with open(wf.datafile("zotero_db.json"), 'r') as f:
			zot_data = json.load(f)
			f.close()

		# Get user ID from settings file
		uid = data['user_id']
			
		set_clipboard(scan_cites(zot_data, item_key, uid))
		
		print prefs['format']


	# If not ODT, then use `pyzotero`
	else:
		from pyzotero import zotero
		from zq_utils import to_unicode

		# Initiate the call to the Zotero API
		zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

		# Return an HTML formatted citation in preferred style
		ref = zot.item(item_key, content='citation', style=prefs['csl'])
		# Remove the <span>...</span> tags and convert to Unicode
		uref = to_unicode(ref[0][6:-7])

		# Export in chosen format
		if prefs['format'] == 'Markdown':
			from dependencies import html2md
			from zq_utils import set_clipboard

			# Convert the HTML to Markdown
			citation = html2md.html2text(uref)

			if prefs['csl'] == 'bibtex':
				citation = '[@' + citation.strip() + ']'

			# Pass the Markdown citation to clipboard
			set_clipboard(citation.strip())

			print "Markdown"

		elif prefs['format'] == 'Rich Text':
			import applescript

			if prefs['csl'] == 'bibtex':
				clean_ref = '[@' + uref.strip() + ']'
				
			# Write html to temporary file
			with open(wf.cachefile(u"temp.html"), 'w') as f:
				f.write(uref.encode('ascii', 'xmlcharrefreplace'))
				f.close

			# Convert html to RTF and copy to clipboard
			a_script = """
				do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
				""".format(wf.cachefile(u"temp.html"))
			applescript.asrun(a_script)

			print "Rich Text"


if __name__ == '__main__':
	wf = Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
	sys.exit(wf.run(main))

   