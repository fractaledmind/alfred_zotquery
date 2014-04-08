#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import os.path
import sys
import unittest
import json
from dependencies import xmltodict
from StringIO import StringIO
from zq_filters import ZotFilter
from zq_actions import ZotAction
from zq_utils import get_clipboard

def setUp():
	pass

def tearDown():
	pass

class FilterTests(unittest.TestCase):

	def setUp(self):
		with open(os.path.join(os.path.dirname(__file__), '__test.json'), 'r') as f:
				self.data = json.load(f)
				f.close()
		self.scopes = ['general', 'creators', 'titles', 'notes', 
						'collections', 'tags', 
						'in-collection', 'in-tag', 
						'attachments']
		self.colls = [['A Personal Collection', 'NHAEA4EJ'], ['open access', 'GU45TP7'], ['book', 'VBMDZBN4'], ['book', 'VBMDZBN4']]
		self.tags = [['tag1', 'xxtag1xx'], ['tag2', 'xxtag2xx'], ['open-access', '9D9XD69I'], ['knowledge-organization', 'DS924HTQ'], ['digital-classics', 'VKIVB3DE'], ['test', 'xxtestxx'], ['misc', 'UM8XT9W9'], ['test1', '9SDK6WVW'], ['hist', 'VAKT9XBD'], ['test2', 'W8GAPKBE']]

	def _capture_output(self, zf):
		old_stdout = sys.stdout
		sys.stdout = mystdout = StringIO()
		zf.filter()
		sys.stdout = old_stdout
		res_dict = xmltodict.parse(mystdout.getvalue())
		return res_dict

	####################################################################
	# Filter Tests
	####################################################################

	# General Scope ----------------------------------------------
	def test_filter_general_len(self):	
		z = ZotFilter('margheim', self.scopes[0], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)
		
	def test_filter_general_title(self):
		z = ZotFilter('nothing', self.scopes[0], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "Chapter with attachment")

	# Creators Scope ----------------------------------------------
	def test_filter_creators_len(self):	
		z = ZotFilter('margheim', self.scopes[1], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)
	
	def test_filter_creators_title(self):
		z = ZotFilter('smïth', self.scopes[1], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "Webpage without tags")

	# Titles Scope ----------------------------------------------
	def test_filter_titles_len(self):
		z = ZotFilter('mindfulness', self.scopes[2], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)

	def test_filter_titles_title(self):
		z = ZotFilter('unicode stuff', self.scopes[2], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "“Unicode stuff”")

	# Notes Scope ----------------------------------------------
	def test_filter_notes_len(self):
		z = ZotFilter('zotquery', self.scopes[3], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)

	def test_filter_notes_title(self):
		z = ZotFilter('medakathalika', self.scopes[3], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "Unlimiting Mindfulness")
		
	# Collections Scope ----------------------------------------------
	def test_filter_collections_len(self):
		z = ZotFilter('book', self.scopes[4], data=self.data, test_group=self.colls)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)

	def test_filter_collections_title(self):
		z = ZotFilter('personal', self.scopes[4], data=self.data, test_group=self.colls)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "A Personal Collection")

	# Tags Scope ----------------------------------------------
	def test_filter_tags_len(self):
		z = ZotFilter('tag', self.scopes[5], data=self.data, test_group=self.tags)
		d = self._capture_output(z)
		self.assertEqual(len(d['items']['item']), 2)

	def test_filter_tags_title(self):
		z = ZotFilter('misc', self.scopes[5], data=self.data, test_group=self.tags)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "misc")

	# In-Collection Scope ----------------------------------------------
	def test_filter_incollection_title(self):
		z = ZotFilter('unlimit', self.scopes[6], data=self.data, test_group="VBMDZBN4")
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "Unlimiting Mindfulness")

	# In-Tag Scope ----------------------------------------------
	def test_filter_intag_title(self):
		z = ZotFilter('selfles', self.scopes[7], data=self.data, test_group="VAKT9XBD")
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['title'], "Selflêss Mind")

	# Attachments Scope ----------------------------------------------
	def test_filter_attachment_arg(self):
		z = ZotFilter('moses', self.scopes[8], data=self.data)
		d = self._capture_output(z)
		self.assertEqual(d['items']['item']['arg'], "/Users/path/to/attachment.pdf")



class ActionTests(unittest.TestCase):

	def setUp(self):
		self.prefs = {"format": "Markdown", "csl": "chicago-author-date", "client": "Standalone"}
		self.settings = {"api_key": "rf8L5AZdrVlK9NMTXDVuotok", "type": "user", "user_id": "1140739"}

	####################################################################
	# Action Tests
	####################################################################

	def test_action_export_citation(self):
		za = ZotAction("0_C3KEUQJW", "cite", settings=self.settings, prefs=self.prefs)
		za.act()
		self.assertEqual(get_clipboard(), "Margheim, Stephen. 2013. “Test Item.” *A Sample Publication* 1 (1): 1–14.")
		
	def test_action_export_ref(self):
		za = ZotAction("0_C3KEUQJW", "ref", settings=self.settings, prefs=self.prefs)
		za.act()
		self.assertEqual(get_clipboard(), "(Margheim 2013)")

	def test_action_export_collection(self):
		zc = ZotAction("c:NHAEA4EJ", "cite_coll", settings=self.settings, prefs=self.prefs)
		zc.act()
		#self.assertEqual(get_clipboard(), expected)

	def test_action_export_tag(self):
		zt = ZotAction("t:Semantics", "cite_tag", settings=self.settings, prefs=self.prefs)
		zt.act()
		#zt.export_group()
		#print get_clipboard().encode('utf-8')
		#print '- - -'



if __name__ == '__main__':
	unittest.main()
