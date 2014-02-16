#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
import subprocess
import re
from dependencies import applescript
from _zotquery import to_unicode
"""
This script gets the path and best query for the chosen PDF 
and writes it to temp file as JSON. 
"""

# Get user input
inp = alp.args()[0] 
#inp = ''

### PART 1: Get PDF path
# If Hotkey
if inp == '':
	# Choose PDF, if necessary
	ascript = """
	tell application "System Events"
		set l to the every process whose background only is false
		set res to {}
		repeat with i from 1 to count of l
			try
				set theprocess to item i of l
				set thetitle to the value of the attribute "AXTitle" of theprocess
				set thewindow to the value of attribute "AXFocusedWindow" of theprocess
				set thefile to the value of attribute "AXDocument" of thewindow as string
				if thetitle is "Finder" then
					tell application "Finder"
						set thefile to (POSIX path of (target of the first window as alias))
					end tell
				end if
				set thefile to my decode_text(thefile)
				set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/Users"}
				set x to text item -1 of thefile
				set AppleScript's text item delimiters to tid
				set path_ to "/Users" & x
				if thefile contains ".pdf" then copy path_ to end of res
			end try
		end repeat
	end tell
	if (count of res) > 1 then
		set doc_l to {}
		repeat with i from 1 to count of res
			set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/"}
			set x to text item -1 of item i of res
			set AppleScript's text item delimiters to tid
			copy x to end of doc_l
		end repeat
		try
			tell application (path to frontmost application as text)
				set chosen_pdf to (choose from list doc_l with title "Add Attachment" with prompt "Act on which PDF?") as string
			end tell
		on error
			tell application "Finder"
				set chosen_pdf to (choose from list doc_l with title "Add Attachment" with prompt "Act on which PDF?") as string
			end tell
		end try

		repeat with i from 1 to count of res
			if item i of res contains chosen_pdf then
				set pdf_path to item i of res
			end if
		end repeat
	else if (count of res) = 1 then
		set pdf_path to item 1 of res
	end if
	return pdf_path

	on decode_text(this_text)
		set flag_A to false
		set flag_B to false
		set temp_char to ""
		set the character_list to {}
		repeat with this_char in this_text
			set this_char to the contents of this_char
			if this_char is "%" then
				set flag_A to true
			else if flag_A is true then
				set the temp_char to this_char
				set flag_A to false
				set flag_B to true
			else if flag_B is true then
				set the end of the character_list to my decode_chars(("%" & temp_char & this_char) as string)
				set the temp_char to ""
				set flag_A to false
				set flag_B to false
			else
				set the end of the character_list to this_char
			end if
		end repeat
		return the character_list as string
	end decode_text
	on decode_chars(these_chars)
		copy these_chars to {indentifying_char, multiplier_char, remainder_char}
		set the hex_list to "123456789ABCDEF"
		if the multiplier_char is in "ABCDEF" then
			set the multiplier_amt to the offset of the multiplier_char in the hex_list
		else
			set the multiplier_amt to the multiplier_char as integer
		end if
		if the remainder_char is in "ABCDEF" then
			set the remainder_amt to the offset of the remainder_char in the hex_list
		else
			set the remainder_amt to the remainder_char as integer
		end if
		set the ASCII_num to (multiplier_amt * 16) + remainder_amt
		return (ASCII character ASCII_num)
	end decode_chars
	""" 
	pdf_path = applescript.asrun(ascript)[0:-1]
else:
	# if File Action, 
	pdf_path = inp

### PART 2: Get query	
# Extract text of first page of PDF
pdf_txt = subprocess.Popen(["./pdftotext", "-q", "-l", "1", pdf_path, "-"], stdout=subprocess.PIPE).communicate()[0]

# DOI regex
# thanks to Alix Axel on Stack Exchange 
# (http://stackoverflow.com/questions/27910/finding-a-doi-in-a-document-or-page)
doi_re = re.compile(r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b')

# ISBN regex
isbn_re = re.compile(r"ISBN((-1(?:(0)|3))?:?\x20(\s)*[0-9]+[- ][0-9]+[- ][0-9]+[- ][0-9]*[- ]*[xX0-9])")

# Use this to have user select keywords
def cap2keywords(pdf_txt):
	cap_words = re.findall(r"\b[A-Z].*?\b", pdf_txt, re.M)
	cap_words = list(set(cap_words))
	poss_search_terms = [x for x in cap_words if len(x) >= 4]

	# Prepare as Applescript List
	as_l = ['"' + x + '"' for x in poss_search_terms]
	as_l = ', '.join(as_l)
	as_l = '{' + as_l + '}'

	# User select key terms
	a_script = """
	try
		tell application (path to frontmost application as text)
			choose from list {0} with prompt "Use which terms for ZotQuery?" with title "ZotQuery" default items item 1 of {0} with multiple selections allowed
		end tell
	on error
		tell application "Finder"
			choose from list {0} with prompt "Use which terms for ZotQuery?" with title "ZotQuery" default items item 1 of {0} with multiple selections allowed
		end tell
	end try
		""".format(as_l)
	res = applescript.asrun(a_script)[0:-1]
	query = ' '.join(res.split(', '))
	return query

# try to get DOI
doi = re.search(doi_re, pdf_txt)
# try to get ISBN
isbn = re.search(isbn_re, pdf_txt)


if doi != None:
	doi = doi.group(1).strip()

if isbn != None:
	isbn = isbn.group(1).strip()


# Check if title page of JSTOR pdf
if 'JSTOR' in pdf_txt:
	jstor_regex = re.compile("^(.*?)Author\\(s\\):\\s(.*?)Source:\\s(.*?)Published by:\\s(.*?)Stable URL:\\s(.*?)Accessed:\\s(.*?)(?:\\n|\\r)", re.S)

	res = re.search(jstor_regex, pdf_txt)

	if res != None:
		title = res.group(1).strip()
		creator = res.group(2).strip()
		info = res.group(3).strip()
		pub = res.group(4).strip()
		url = res.group(5).split(' ')[0]
		date = res.group(6).strip()

		query = creator + ' ' + title
	else:
		query = cap2keywords(pdf_txt)

# If not JSTOR, ask user for keywords
else:
	query = cap2keywords(pdf_txt)


### PART 3: Story Path and Query
# Store the paths in non-volatile storage
with open(alp.cache(join='temp_attach_path.txt'), 'w') as f:
	d = {'path': pdf_path, 'doi': doi, 'isbn': isbn, 'query': query}
	_json = json.dumps(d, sort_keys=False, indent=4, separators=(',', ': '))
	final_json = to_unicode(_json, encoding='utf-8')
	f.write(final_json.encode('utf-8'))
	f.close()

ascript = """
	tell application "Alfred 2" to search "z:pdf" 
"""
applescript.asrun(ascript)
