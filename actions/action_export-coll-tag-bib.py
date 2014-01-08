#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import re
from dependencies.pyzotero import zotero
from dependencies import html2md, alp


"""
This script exports a Bibliography of Markdown formatted, Chicago-style citations for the selected collection.
"""

inp = sys.argv[1].split(':')


try:
	# Get the Library ID and API Key from the settings file
	settings = alp.local(join="settings.json")
	cache_file = open(settings, 'r')
	data = json.load(cache_file)

	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	if inp[0] == 'c':
		try:
			# Get the item key from the system input
			coll_key = inp[1]
			#coll_key = 'GXWGBRJD'

			# Return a list of HTML formatted citations in Chicago style
			cites = zot.collection_items(coll_key, content='bib', style='chicago-author-date')
		
			try:	
				md_cites = []
				for ref in cites:
					# Convert the HTML to Markdown
					citation = html2md.html2text(ref).encode('utf-8')

					# Remove url, if there
					result = re.sub("(?:http|doi)(.*?)$", "", citation)

					# Append the Markdown citation to a new list
					md_cites.append(result)

				# Sort that list alphabetically
				sorted_md = sorted(md_cites)
				# Begin with WORKS CITED header
				sorted_md.insert(0, 'WORKS CITED')

				# Output the result as a well-formatted string
				print '\n\n'.join(sorted_md)

			# Log the various possible error points.	
			except:
				alp.log('Error! Could not format bibliography.')
				print 'Error! Could not format bibliography.'
		except:
			alp.log('Error! Not connected to internet.')
			print 'Error! Not connected to internet.'

	elif inp[0] == 't':
		try:
			# Get the item key from the system input
			tag_key = inp[1]
			#coll_key = 'Hippocrates'

			# Return a list of HTML formatted citations in Chicago style
			cites = zot.tag_items(tag_key, content='bib', style='chicago-author-date')
		
			try:	
				md_cites = []
				for ref in cites:
					# Convert the HTML to Markdown
					citation = html2md.html2text(ref).encode('utf-8')

					# Remove url, if there
					result = re.sub("(?:http|doi)(.*?)$", "", citation)

					# Append the Markdown citation to a new list
					md_cites.append(result)

				# Sort that list alphabetically
				sorted_md = sorted(md_cites)
				# Begin with WORKS CITED header
				sorted_md.insert(0, 'WORKS CITED')

				# Output the result as a well-formatted string
				print '\n\n'.join(sorted_md)

			# Log the various possible error points.	
			except:
				alp.log('Error! Could not format bibliography.')
				print 'Error! Could not format bibliography.'
		except:
			alp.log('Error! Not connected to internet.')
			print 'Error! Not connected to internet.'
except:
	alp.log('Error! Improper Zotero API data.')
	print 'Error! Improper Zotero API data.'
