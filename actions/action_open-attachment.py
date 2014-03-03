#!/usr/bin/python
# encoding: utf-8
import sys
from workflow import Workflow

def main(wf):
	import json
	import os.path
	import subprocess
	from dependencies import applescript

	# Get Zotero data from JSON cache
	with open(wf.datafile(u"zotero_db.json"), 'r') as f:
		zot_data = json.load(f)
		f.close()

	query = wf.args[0]

	# if query is full file path
	if os.path.isfile(query):
		subprocess.Popen(['open', query], shell=False, stdout=subprocess.PIPE)
	# if query is item key
	else:
		# Get the item's attachement path and attachment key
		for item in zot_data:
			if query == item['key']:
				for jtem in item['attachments']:
					path = jtem['path']
					key = jtem['key']

		if os.path.isfile(path):
		    # Open file in default application
		    subprocess.Popen(['open', path], shell=False, stdout=subprocess.PIPE)
		else:
			# Open the attachment in Zotero
			a_script = """
			if application id "org.zotero.zotero" is not running then
				tell application id "org.zotero.zotero" to launch
			end if
			delay 0.5
			tell application id "org.zotero.zotero"
				activate
				delay 0.3
				open location "zotero://select/items/0_{0}"
			end tell
			""".format(key)
			applescript.asrun(a_script)

if __name__ == '__main__':
	wf = Workflow()
	sys.exit(wf.run(main))