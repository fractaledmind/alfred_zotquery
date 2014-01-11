#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import sys
import json
import re
from dependencies.pyzotero import zotero
from dependencies import html2md


"""
This script exports a Markdown formatted, Chicago-style citation of the selected item.
"""

# Get the Library ID and API Key from the settings file
settings = alp.local(join="settings.json")
cache_file = open(settings, 'r')
data = json.load(cache_file)

try:
	# Initiate the call to the Zotero API
	zot = zotero.Zotero(data['user_id'], data['type'], data['api_key'])

	try:
		# Get the item key from the system input
		item_key = sys.argv[1]
		#item_key = '7VT63AQG'

		try:
			# Return an HTML formatted citation in APA style
			ref = zot.item(item_key, content='bib', style='chicago-author-date')

			try:
				# Convert the HTML to Markdown
				citation = html2md.html2text(ref[0]).encode('utf-8')

				try:
					# Remove url, DOI, and "pp. ", if there
					result = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
					# Replace "_..._" MD italics with "*...*"
					result = re.sub("_(.*?)_", "*\\1*", result)

					# Pass the Markdown citation to output
					print result
				except:
					alp.log('Error! RegEx failure.')
					print 'Error! RegEx failure.'
			except:
				alp.log('Error! Could not convert from HTML to MD.')
				print 'Error! Could not convert from HTML to MD.'
		except:
			alp.log('Error! No result from Zotero.')
			print 'Error! No result from Zotero.'
	except:
		alp.log('Error! Could not read input.')
		print 'Error! Could not read input.'
except:
	alp.log('Error! Not connected to internet.')
	print 'Error! Not connected to internet.'