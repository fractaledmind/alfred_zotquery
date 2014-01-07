#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dependencies import alp
import sys
from _zotquery import to_unicode

"""
This script writes the name of the Tag chosen in z:tag to a file for reading later. 
"""
	
input = sys.argv[1]
final = to_unicode(input, encoding='utf-8')

# Write the inputted Collection name to a temporary file
temp = alp.cache(join='tag_query_result.txt')
file = open(temp, 'w')
file.write(final).encode('utf-8')
file.close()
