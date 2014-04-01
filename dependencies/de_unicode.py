#!/usr/bin/python
# encoding: utf-8
import os
import sys
from workflow.workflow import Workflow

def main(wf):
	import json
	j = """
	{
	        "id": 1,
	        "key": "2MFFJAWU",
	        "type": "article-journal",
	        "creators": [
	            {
	                "type": "author",
	                "family": "Dihle",
	                "given": "Albrecht"
	            }
	        ],
	        "data": {
	            "volume": 106,
	            "source": "Google Scholar",
	            "container-title": "Philologus",
	            "issued": "1962",
	            "title": "Herodot und die Sophistik",
	            "issue": 1062,
	            "page": "207\u2013220"
	        },
	        "zot-collections": [
	            {
	                "name": "Ev and Inference in Herodotus",
	                "key": "NHAEA4EJ"
	            }
	        ],
	        "zot-tags": [],
	        "attachments": [],
	        "notes": []
	    }
	"""
	print json.loads(j)

if __name__ == '__main__':
	wf = Workflow()
	sys.exit(wf.run(main))