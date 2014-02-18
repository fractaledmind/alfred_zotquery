#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import json
from dependencies import applescript

inp = alp.args()[0]
#inp = "attach"

with open(alp.cache(join='temp_attach_path.txt'), 'r') as f:
	data = json.load(f)
	f.close()

if inp == 'attach':
	a_script = """
		tell application "Alfred 2" to search "z:attach %s"
		""" % data['query']
	res = applescript.asrun(a_script)

elif inp == 'create':
	a_script = """
		tell application "Alfred 2" to search "z2:create %s"
		""" % data['query']
	res = applescript.asrun(a_script)