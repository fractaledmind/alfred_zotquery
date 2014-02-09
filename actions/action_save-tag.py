#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
"""
This script writes the name of the Tag chosen in z:tag to a file for reading later. 
"""
# Get user input
inp = alp.args()[0]
#inp = 'History'

# Write the inputted Tag name to a temporary file
with open(alp.cache(join='tag_query_result.txt'), 'w') as f:
	f.write(inp.encode('utf-8'))
	f.close()
	