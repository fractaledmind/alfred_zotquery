#!/usr/bin/python
# encoding: utf-8
import sys
import os.path
from workflow import Workflow

def main(wf):
	wf.add_item(u"Root", u"Open ZotQuery's Root Folder?", valid=True, arg='workflow:openworkflow', icon='icons/n_folder.png')
	wf.add_item(u"Storage", u"Open ZotQuery's Storage Folder?", valid=True, arg='workflow:opendata', icon='icons/n_folder.png')
	wf.add_item(u"Cache", u"Open ZotQuery's Cache Folder?", valid=True, arg='workflow:opencache', icon='icons/n_folder.png')
	wf.add_item(u"Logs", u"Open ZotQuery's Logs?", valid=True, arg='workflow:openlog', icon='icons/n_folder.png')

	wf.send_feedback()
		
if __name__ == '__main__':
	wf = Workflow()
	sys.exit(wf.run(main))
