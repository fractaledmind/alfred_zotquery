#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow import Workflow

def main(wf):
	import json
	from zq_utils import prepare_feedback

	# Get current Zotero data from JSON cache
	with open(wf.datafile('zotero_db.json'), 'r') as f:
		curr_data = json.load(f)
		f.close()
	curr_ids = [item['id'] for item in curr_data]

	# Get previous Zotero data from JSON cache
	with open(wf.datafile('old_db.json'), 'r') as f:
		old_data = json.load(f)
		f.close()
	old_ids = [item['id'] for item in old_data]

	# Get list of newly added items
	new_ids = list(set(curr_ids) - set(old_ids))

	new_items = []
	for i in new_ids:
		new_items += list((item for item in curr_data if item['id'] == i))

	res = prepare_feedback(new_items)
	if res != []:
		for a in res:
			wf.add_item(**a)
		wf.send_feedback()
	else:
		# If no results
		wf.add_item(u"No new items found.", u"There aren't any items recently added to your Zotero library.", 
			icon=u"icons/n_error.png")
		wf.send_feedback()
	
if __name__ == '__main__':
	wf = Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
	sys.exit(wf.run(main))
