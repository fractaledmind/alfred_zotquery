#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp

"""
This script appends the formatted citation to a bibliography file.
"""

# Get input
inp = alp.args()[0]

# Append final, formatted input to biblio file
with open(alp.cache(join='bibliography.txt'), 'a') as f:
	f.write(inp.encode('utf-8'))
	f.write('')
	f.close()
	