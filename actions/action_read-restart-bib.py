#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
from dependencies import applescript
import alp
import re

"""
This script reads, formats, outputs, and restarts the cached bibliography file.
"""

# First, ensure that Configuration has taken place
if os.path.exists(alp.storage(join="first-run.txt")):

	with open(alp.cache(join='bibliography.txt'), 'r') as f:
		data = f.read()
		f.close()

	# Remove escaped spaces
	result = re.sub(r"\\\s", " ", data)
	# Remove escaped parentheses
	result = re.sub(r"\\\((.*?)\\\)", "(\\1)", result)

	# Convert the string to a list of citations
	l = result.split('\n\n')
	# Sort that list alphabetically
	sorted_l = sorted(l)

	# Begin with WORKS CITED
	if sorted_l[0] == '':
	sorted_l[0] = 'WORKS CITED'
	else:
	sorted_l.insert(0, 'WORKS CITED')

	# Output the result as a well-formatted string
	print '\n\n'.join(sorted_l)

	# Restart the bibliography file
	with open(alp.cache(join='bibliography.txt'), 'w') as f:
		f.write('')
		f.close()

# Not configured
else:
	a_script = """
			tell application "Alfred 2" to search "z:config"
			"""
	applescript.asrun(a_script)