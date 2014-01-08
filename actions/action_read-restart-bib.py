#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
from dependencies import alp

"""
This script reads, formats, outputs, and restarts the cached bibliography file.
"""

bib = alp.cache(join='bibliography.txt')
bib_file = open(bib, 'r')
data = bib_file.read()
bib_file.close()

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
bib_file = open(bib, 'w')
data = bib_file.write('')
bib_file.close()