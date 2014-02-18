#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import requests
import re

inp = alp.args()[0]
#inp = 'horace odes'
# Use crossref metadata search (beta)
params = {'q': inp, 'rows': '10'}
r = requests.get('http://search.labs.crossref.org/dois', params=params)

alp_res = []

# Option to search Google Scholar if no results at CrossRef found
att_dict = {'title': "Not Here? Search Google Scholar?", 'subtitle': "Search Google Scholar?", 'valid': True, 'arg': 'gscholar', 'icon': 'icons/gscholar.png'}
att_item = alp.Item(**att_dict)
alp_res.append(att_item)

# Prepare crossref results for Alfred
for item in r.json():
	doi = item['doi'].split('dx.doi.org/')[1]
	title = item['title'].strip()

	info = item['fullCitation']
	citation = re.sub("<(.*?)>", "",info).strip()
	
	att_dict = {'title': title, 'subtitle': citation, 'valid': True, 'arg': doi, 'icon': 'icons/n_folder.png'}
	att_item = alp.Item(**att_dict)
	alp_res.append(att_item)

alp.feedback(alp_res)
