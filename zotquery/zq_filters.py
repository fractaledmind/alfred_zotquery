#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2014 Stephen Margheim <stephen.margheim@gmail.com>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
#
"""
Data filters for ZotQuery, an Alfred workflow for Zotero.
"""
from __future__ import unicode_literals
import sys
sys.path.insert(0, 'alfred-workflow.zip')
import workflow
import os.path
import json
import zq_utils as z
from dependencies import applescript


class ZotFilter(object):
	
	def __init__(self, query, scope, data=[], test_group=None, personal_only=False):
		self.wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
		self.query = query
		self.scope = scope

		if self.first_run_test() and self.query_len_test(): pass
			
		if data == []:
			with open(self.wf.datafile("zotero_db.json"), 'r') as f:
				self.data = json.load(f)
				f.close()
			if personal_only == True:
				personal_data = []
				ids = []
				for i in self.data:
					if i['zot-collections'] != []:
						for c in i['zot-collections']:
							if c['group'] == 'personal':
								if not i['id'] in ids:
									personal_data.append(i)
									ids.append(i['id'])
				self.data = personal_data
		else:
			self.data = data

		self.test_group = test_group

	####################################################################
	# Helper functions
	####################################################################

	def first_run_test(self):
		if not os.path.exists(self.wf.datafile("first-run.txt")):
			applescript.asrun('tell application "Alfred 2" to search "z:config"')
			sys.exit(0)
		else: return True

	def query_len_test(self):
		if len(self.query) <= 2:
			self.wf.add_item("Error!", "Need at least 3 letters to execute search", 
				icon="icons/n_delay.png")
			self.wf.send_feedback()
			sys.exit(0)
		else: return True

	def no_results(self):
		self.wf.add_item("Error!", "No results found.", 
						icon="icons/n_error.png")
		self.wf.send_feedback()

	####################################################################
	# API method
	####################################################################

	def filter(self):
		if self.scope in ['general', 'creators', 'titles', 'notes']:
			self.filters_simple()

		elif self.scope in ['collections', 'tags']:
			self.filters_groups()

		elif self.scope in ['in-collection', 'in-tag']:
			self.filters_in_groups()

		elif self.scope == 'attachments':
			self.filters_atts()

		elif self.scope == 'debug':
			self.filters_debug()

		elif self.scope == 'new':
			return self.filters_new()

	####################################################################
	# Sub-Methods
	####################################################################

	def filters_simple(self):
		res = self.wf.filter(self.query, self.data, key=lambda x: z.zot_string(x, self.scope))
		if res != []:
			# Format matched items for display
			prep_res = z.prepare_feedback(res)	
			for item in prep_res:
				self.wf.add_item(**item)
			self.wf.send_feedback()
		else:
			self.no_results()

	def filters_groups(self):
		group_data = self._get_group_data(self.test_group)
		if group_data != []:
			res = self.wf.filter(self.query, group_data, key=lambda x: x[0])
			if res != []:
				if self.scope == "collections":
					_pre = "c:"
				elif self.scope == "tags":
					_pre = "t:"
				for item in res:
					self.wf.add_item(item[0], self._sub, 
						arg=_pre + item[1], 
						valid=True, 
						icon=self._icon)
				self.wf.send_feedback()
			else:
				self.no_results()
		else:
			self.no_results()

	def filters_in_groups(self):
		ingroup_data = self._get_ingroup_data(self.test_group)
		if ingroup_data != []:
			res = self.wf.filter(self.query, ingroup_data, key=lambda x: z.zot_string(x))
			if res != []:
				prep_res = z.prepare_feedback(res)	
				for item in prep_res:
					self.wf.add_item(**item)
				self.wf.send_feedback()
			else:
				self.no_results()
		else:
			self.no_results()

	def filters_atts(self):
		atts_data = self._get_atts_data()
		if atts_data != []:
			res = self.wf.filter(self.query, atts_data, key=lambda x: z.zot_string(x))
			if res != []:
				for item in res:
					info = z.info_format(item)
					title = item['data']['title']
					sub = info[0] + ' ' + info[1]
					self.wf.add_item(title, sub, 
						arg=item['attachments'][0]['path'], 
						valid=True,
						type='file',
						icon='icons/n_pdf.png')
				self.wf.send_feedback()
			else:
				self.no_results()
		else:
			self.no_results()

	def filters_debug(self):
		self.wf.add_item("Root", "Open ZotQuery's Root Folder?", valid=True, arg='workflow:openworkflow', icon='icons/n_folder.png')
		self.wf.add_item("Storage", "Open ZotQuery's Storage Folder?", valid=True, arg='workflow:opendata', icon='icons/n_folder.png')
		self.wf.add_item("Cache", "Open ZotQuery's Cache Folder?", valid=True, arg='workflow:opencache', icon='icons/n_folder.png')
		self.wf.add_item("Logs", "Open ZotQuery's Logs?", valid=True, arg='workflow:openlog', icon='icons/n_folder.png')
		self.wf.send_feedback()

	def filters_new(self):
		curr_ids = [item['id'] for item in self.data]
		# Get previous Zotero data from JSON cache
		with open(self.wf.datafile('old_db.json'), 'r') as f:
			old_data = json.load(f)
			f.close()
		old_ids = [item['id'] for item in old_data]
		# Get list of newly added items
		new_ids = list(set(curr_ids) - set(old_ids))
		new_items = []
		for i in new_ids:
			new_items += [item for item in self.data if item['id'] == i]
		#return new_items
		res = z.prepare_feedback(new_items)
		if res != []:
			for a in res:
				self.wf.add_item(**a)
			self.wf.send_feedback()
		else:
			self.no_results()

	####################################################################
	# Get sub-sets of data methods
	####################################################################

	def _get_group_data(self, test_group):
		if test_group == None:
			import sqlite3
			conn = sqlite3.connect(self.wf.datafile("zotquery.sqlite"))
			cur = conn.cursor()
			
			if self.scope == "collections":
				sql_query = """select collections.collectionName, collections.key
				from collections"""
				self._sub = "Collection"
				self._icon = "icons/n_collection.png"
			elif self.scope == "tags":
				sql_query = """select tags.name, tags.name
				from tags"""
				self._sub = "Tag"
				self._icon = "icons/n_tag.png"

			group_data = cur.execute(sql_query).fetchall()
			conn.close()
		else:
			group_data = test_group
			self._sub = "Test"
			self._icon = "icon.png"
		return group_data	

	def _get_ingroup_data(self, test_group):
		term = self.scope.split('-')[1]
		if test_group == None:
			with open(self.wf.cachefile("{0}_query_result.txt").format(term), 'r') as f:
				_inp = f.read().decode('utf-8')
				f.close()
		else:
			_inp = test_group
		
		_items = []
		for item in self.data:
			for jtem in item['zot-{0}s'.format(term)]:
				if _inp == jtem['key']: 
					_items.append(item)
		return _items
	
	def _get_atts_data(self):
		_items = []
		for item in self.data:
			if item['attachments'] != []:
				_items.append(item)
		return _items
