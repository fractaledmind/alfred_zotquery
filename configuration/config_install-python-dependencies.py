#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp
import subprocess
import alp
import re
import time
from dependencies import applescript

# List of all modules used in ZotQuery
modules = ['sqlite3', 'json', 'collections', 'os', 'shutil', 're', 'subprocess', 'time', 'sys', 'plistlib', 'unicodedata', 'codecs', 'xml', 'copy', 'operator', 'types', 'calendar', 'datetime', 'math', 'struct', 'urllib', 'htmlentitydefs', 'StringIO', 'sgmllib', 'urlparse', 'setuptools', 'requests', 'socket', 'feedparser', 'uuid', 'hashlib', 'pytz', 'mimetypes']

# Check if any module not found
nots = []
for m in modules:
	try:
	    imp.find_module(m)
	except ImportError:
	    nots.append(m)

# Prepare path to ZotQuery icon
icon_path = re.sub('/', ':', alp.local(join='icon.png'))

if nots != []:
	# Check if user wishes to install/update necessary Python modules
	a_script = """
	tell application "Finder"
		try
			set icon_ to "Macintosh HD%s" as alias
			set choice to display dialog "ZotQuery requires certain basic Python modules which your computer does not currently have installed." & return & return & "Can ZotQuery install these modules?" with title "ZotQuery Dependencies" buttons {"Install", "Cancel"} default button 1 cancel button 2 with icon icon_
		on error
			set choice to display dialog "ZotQuery requires certain basic Python modules which your computer does not currently have installed." & return & return & "Can ZotQuery install these modules?" with title "ZotQuery Dependencies" buttons {"Install", "Cancel"} default button 1 cancel button 2
		end try
		if button returned of choice = "Install" then
			return 1
		else
			return 0
		end if
	end tell
		""" % icon_path
	res = applescript.asrun(a_script)[0:-1]

	# If yes to install
	if res[0] == '1':
		# If necessary, install pip
		devnull = open('/dev/null', 'w')
		if subprocess.call(["which", "pip"], stdout=devnull, stderr=devnull):
			a_script = """
			set theScript_ to "sudo easy_install pip"
			do shell script theScript_ with administrator privileges
			"""
			applescript.asrun(a_script)
			time.sleep(1)

		# Install all missing modules
		for m in nots:
			a_script = """
			set theScript_ to "sudo pip install  %s"
			do shell script theScript_ with administrator privileges
			delay 0.5
			set theScript_ to "sudo pip install  --upgrade %s"
			do shell script theScript_ with administrator privileges
			""" % m
			p = applescript.asrun(a_script)[0:-1]
			print p
			time.sleep(1)

	# If no to install
	else:
		a_script = """
	tell application "Finder"
		try
			set icon_ to "Macintosh HD%s" as alias
			display dialog "Warning! Without these Python modules, ZotQuery will not function properly." with title "ZotQuery Dependencies" with icon icon_
		on error
			display dialog "Warning! Without these Python modules, ZotQuery will not function properly." with title "ZotQuery Dependencies"
		end try
	end tell	
		""" % icon_path
		applescript.asrun(a_script)
		print "Warning! Without these Python modules, ZotQuery will not function properly."
else:
	a_script = """
	tell application "Finder"
		try
			set icon_ to "Macintosh HD%s" as alias
			display dialog "ZotQuery dependencies are up-to-date." with title "ZotQuery Dependencies" with icon icon_
		on error
			display dialog "ZotQuery dependencies are up-to-date." with title "ZotQuery Dependencies"
		end try
	end tell
	""" % icon_path
	applescript.asrun(a_script)
