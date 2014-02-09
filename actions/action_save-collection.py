#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
"""
This script writes the key of the Collection chosen in z:col to a file for reading later. 
"""
# Get user input
inp = alp.args()[0]
#inp = 'Test 1 2'

# Write the inputted Collection key to a temporary file
with open(alp.cache(join='collection_query_result.txt'), 'w') as f:
	f.write(inp.encode('utf-8'))
	f.close()
	