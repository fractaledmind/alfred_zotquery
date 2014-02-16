#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import re
import json

with open(alp.cache(join='temp_attach_path.txt'), 'r') as f:
	data = json.load(f)
	f.close()

pdf_title = data['path'].split('/')[-1]

alp_res = []
att_dict = {'title': 'Attach', 'subtitle': "Attach %s to Zotero item" % pdf_title, 'valid': True, 'arg': 'attach', 'icon': 'icons/n_pdf.png'}
create_dict = {'title': 'Create and Attach', 'subtitle': "Create new Zotero item and Attach %s" % pdf_title, 'valid': True, 'arg': 'create', 'icon': 'icons/att_pdf.png'}
att_item = alp.Item(**att_dict)
create_item = alp.Item(**create_dict)
alp_res.append(att_item)
alp_res.append(create_item)
alp.feedback(alp_res)