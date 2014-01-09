#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from dependencies import alp

"""
This script appends the formatted citation to a bibliography file.
"""
# Get input
inp = sys.argv[1]

# Append final, formatted input to biblio file
bib = alp.cache(join='bibliography.txt')
bib_file = open(bib, 'a')
bib_file.write(inp)
bib_file.write('')
bib_file.close()