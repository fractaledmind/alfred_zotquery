#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import alp
import sys
from _zotquery import to_unicode

"""
This script writes the name of the Collection chosen in z:col to a file for reading later. 
"""
	
input = sys.argv[1]
final = to_unicode(input, encoding='utf-8')

# Write the inputted Collection name to a temporary file
temp = alp.cache(join='collection_query_result.txt')
file = open(temp, 'w')
file.write(final).encode('utf-8')
file.close()
