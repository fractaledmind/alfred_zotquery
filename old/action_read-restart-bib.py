#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow import Workflow

def main(wf):
	import os.path
	import json
	import applescript
	"""
	This script reads, formats, outputs, and restarts the cached bibliography file.
	"""

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

	# First, ensure that Configuration has taken place
	if os.path.exists(wf.datafile(u"first-run.txt")):

		# Export in chosen format
		if prefs['format'] == 'Markdown':
			from zq_utils import set_clipboard

			with open(wf.cachefile(u"temp_bibliography.txt"), 'r') as f:
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
			set_clipboard('\n\n'.join(sorted_l))

			print "Markdown"

			# Restart the bibliography file
			with open(wf.cachefile(u"temp_bibliography.txt"), 'w') as f:
				f.write('')
				f.close()


		if prefs['format'] == 'Rich Text':
			# Read html from temporary bib file
			with open(wf.cachefile(u"temp_bibliography.html"), 'r') as f:
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
			with open(wf.cachefile(u"temp_bibliography.html"), 'w') as f:
				f.write(html_string)
				f.close()

			# Convert html to RTF and copy to clipboard
			a_script = """
				do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
				""".format(wf.cachefile(u"temp_bibliography.html"))
			applescript.asrun(a_script)

			print "Rich Text"

			# Write blank file to bib file
			with open(wf.cachefile(u"temp_bibliography.html"), 'w') as f:
				f.write('')
				f.close()

	# Not configured
	else:
		a_script = """
			tell application "Alfred 2" to search "z:config"
			"""
		applescript.asrun(a_script)


if __name__ == '__main__':
	wf = Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
	sys.exit(wf.run(main))