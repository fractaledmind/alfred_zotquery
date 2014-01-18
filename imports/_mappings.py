#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from _zotquery import to_unicode

"""
This script defines 3 functions for translating Zotero's terminology to the standardized CSL-JSON format. Each function takes a Zotero term as input and outputs the corresponding CSL term. The mapping relationships are defined in the zotero-csl_mappings.json file. Since .json is not ideal for value-based queries, and since parsing the entire tree as XML on each call takes too much time, these functions utilize merely Regular Expressions. 
"""

dir_path = os.getcwd()
mappings_path = dir_path + '/_zotero-csl_mappings.json'

mappings = open(mappings_path).read()

def trans_fields(q):

	def field_search(v):
		# Search for direct mapping of Zotero field type to CSL field type
		regex = r'"@zField": "' + v + '",\n\s*"@cslField": "(.*?)"$'
		x = re.findall(regex, mappings, re.M)
		if not x == []:
			return x[0]
			
	# See if Zotero field has direct mapping to CSL
	query1 = field_search(q)
	
	if query1 == None:
		# If not, search for the base field of that particular field
		regex = r'"@value": "' + q + '",\n\s*"@baseField":\s"(.*?)"$'
		x = re.findall(regex, mappings, re.M)
		if not x == []:
			res = field_search(x[0])
			return to_unicode(res, encoding='utf-8')
		else:
			return to_unicode(q, encoding='utf-8')
	else:
		return to_unicode(query1, encoding='utf-8')


def trans_types(q):
	
	regex = r'"@zType": "' + q + '",\n\s*"@cslType": "(.*?)"'
	x = re.findall(regex, mappings, re.M)
	if not x == []:
		return to_unicode(x[0], encoding='utf-8')
	else:
		return to_unicode(q, encoding='utf-8')
		

def trans_creators(q):
	
	regex = r'"@zField": "' + q + '",\n\s*"@cslField": "(.*?)"'
	x = re.findall(regex, mappings, re.M)
	if not x == []:
		return to_unicode(x[0], encoding='utf-8')
	else:
		return to_unicode(q, encoding='utf-8')
