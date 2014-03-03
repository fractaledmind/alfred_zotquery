#!/usr/bin/python
# encoding: utf-8
import os
import re
from _zotquery import to_unicode

"""
This script defines 3 functions for translating Zotero's terminology to the standardized CSL-JSON format. 
Each function takes a Zotero term as input and outputs the corresponding CSL term. 
The mapping relationships are defined in the _zotero-csl_mappings.json file. 
Since JSON is not ideal for value-based queries, 
and since parsing the entire tree as XML on each call takes too much time, 
these functions utilize merely Regular Expressions. 
"""

dir_path = os.getcwd()
mappings_path = dir_path + '/_zotero-csl_mappings.json'
mappings = open(mappings_path).read()

def trans_fields(q, to):

	def field_search(v, too):
		zot2csl_regex = r'"@zField":\s"' + v + r'",\n\s*"@cslField":\s"(.*?)"$'
		csl2zot_regex = r'"@zField":\s"(.*?)",\n\s*"@cslField":\s"' + v + r'"$'

		if too == 'csl':
			x = re.findall(zot2csl_regex, mappings, re.M)
			if not x == []:
				return x[0]
		elif too == 'zot':
			x = re.findall(csl2zot_regex, mappings, re.M)
			if not x == []:
				return x[0]
			
	# See if Zotero field has direct mapping to CSL
	query1 = field_search(q, to)
	
	if query1 == None:
		# If not, search for the base field of that particular field
		zot2csl_regex = r'"@value":\s"' + q + r'",\n\s*"@baseField":\s"(.*?)"$'
		csl2zot_regex = r'"@value":\s"(.*?)",\n\s*"@baseField":\s"' + q + r'"$'

		if to == 'csl':
			x = re.findall(zot2csl_regex, mappings, re.M)
			if not x == []:
				res = field_search(x[0], to)
				return to_unicode(res, encoding='utf-8')
			else:
				return to_unicode(q, encoding='utf-8')
		elif to == 'zot':
			x = re.findall(csl2zot_regex, mappings, re.M)
			if not x == []:
				res = field_search(x[0], to)
				return to_unicode(res, encoding='utf-8')
			else:
				return to_unicode(q, encoding='utf-8')
	else:
		return to_unicode(query1, encoding='utf-8')


def trans_types(q, to):
	
	zot2csl_regex = r'"@zType":\s"' + q + r'",\n\s*"@cslType":\s"(.*?)"'
	csl2zot_regex = r'"@zType":\s"(.*?)",\n\s*"@cslType":\s"' + q + r'"'

	if to == "csl":
		x = re.findall(zot2csl_regex, mappings, re.M)
		if not x == []:
			return to_unicode(x[0], encoding='utf-8')
		else:
			return to_unicode(q, encoding='utf-8')
	elif to == "zot":
		x = re.findall(csl2zot_regex, mappings, re.M)
		if not x == []:
			return to_unicode(x[0], encoding='utf-8')
		else:
			return to_unicode(q, encoding='utf-8')
		

def trans_creators(q, to):
	
	zot2csl_regex = r'"@zField":\s"' + q + r'",\n\s*"@cslField":\s"(.*?)"'
	csl2zot_regex = r'"@zField":\s"(.*?)",\n\s*"@cslField":\s"' + q + r'"'

	if to == 'csl':
		x = re.findall(zot2csl_regex, mappings, re.M)
		if not x == []:
			return to_unicode(x[0], encoding='utf-8')
		else:
			return to_unicode(q, encoding='utf-8')
	elif to == 'zot':
		x = re.findall(csl2zot_regex, mappings, re.M)
		if not x == []:
			return to_unicode(x[0], encoding='utf-8')
		else:
			return to_unicode(q, encoding='utf-8')