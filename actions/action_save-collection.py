#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
from _zotquery import to_unicode
"""
This script writes the key of the Collection chosen in z:col to a file for reading later. 
"""
# Get user input
inp = alp.args()[0]
inp = to_unicode(inp, encoding='utf-8')
#inp = u'Test Collection'

# Write the inputted Collection key to a temporary file
with open(alp.cache(join='collection_query_result.txt'), 'w') as f:
	f.write(inp.encode('utf-8'))
	f.close()
	