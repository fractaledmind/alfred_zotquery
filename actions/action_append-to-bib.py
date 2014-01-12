#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import sys

"""
This script appends the formatted citation to a bibliography file.
"""

try:
	# Get input
	inp = sys.argv[1]

	try:
		# Append final, formatted input to biblio file
		bib = alp.cache(join='bibliography.txt')
		bib_file = open(bib, 'a')
		bib_file.write(inp)
		bib_file.write('')
		bib_file.close()
	except:
		alp.log('Error! Could not append to cache.')
		print 'Error! Could not append to cache.'	
except:
	alp.log('Error! Could not read input.')
	print 'Error! Could not read input.'