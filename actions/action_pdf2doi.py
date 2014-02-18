#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import subprocess
import re
import requests
import sys
from dependencies import applescript


#arg = sys.argv[1]

with open(alp.cache(join='temp_attach_path.txt'), 'r') as f:
	data = f.read()
	f.close()

pdffile = re.sub(r"\\\s", " ", data)

# Extract text of first page of PDF
pdf_txt = subprocess.Popen(["./pdftotext", "-q", "-l", "1", pdffile, "-"], stdout=subprocess.PIPE).communicate()[0]

# DOI regex
# thanks to Alix Axel on Stack Exchange 
# (http://stackoverflow.com/questions/27910/finding-a-doi-in-a-document-or-page)
doi_re = re.compile(r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b')

# try to get DOI
doi = re.search(doi_re, pdf_txt)

if doi == None:
	 # couldn't find DOI, grab the first dozen capitalized words as a fallback
	cap_words = re.findall(r"\b[A-Z].*?\b", pdf_txt, re.M)
	cap_words = list(set(cap_words))
	poss_search_terms = [x for x in cap_words if len(x) >= 4]

	# Prepare as Applescript List
	as_l = ['"' + x + '"' for x in poss_search_terms]
	as_l = ', '.join(as_l)
	as_l = '{' + as_l + '}'

	# User select key terms
	a_script = """
		tell application (path to frontmost application as text)
			choose from list {0} with prompt "Use which terms for ZotQuery?" with title "ZotQuery" default items item 1 of {0} with multiple selections allowed
		end tell
		""".format(as_l)
	res = applescript.asrun(a_script)[0:-1]
	query = ' '.join(res.split(', '))
else:
	query = doi.group(1)



print query

