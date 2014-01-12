#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import sys
from _zotquery import to_unicode

"""
This script writes the key of the Collection chosen in z:col to a file for reading later. 
"""

try:
	inp = sys.argv[1]
	final = to_unicode(inp, encoding='utf-8')

	try:
		# Write the inputted Collection key to a temporary file
		temp = alp.cache(join='collection_query_result.txt')
		file = open(temp, 'w')
		file.write(final).encode('utf-8')
		file.close()
	except:
		alp.log('Error! Could not write to cache.')
		print 'Error! Could not write to cache.'
except:
	alp.log('Error! Failure to receive and encode input.')
	print 'Error! Failure to receive and encode input.'