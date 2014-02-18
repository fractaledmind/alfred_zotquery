#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
from _zotquery import to_unicode
"""
This script writes the name of the Tag chosen in z:tag to a file for reading later. 
"""
# Get user input
inp = alp.args()[0]
inp = to_unicode(inp, encoding='utf-8')

# Write the inputted Tag name to a temporary file
with open(alp.cache(join='tag_query_result.txt'), 'w') as f:
	f.write(inp.encode('utf-8'))
	f.close()
	