#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import sys
import sqlite3
import subprocess
from time import time

import utils
from workflow import Workflow
from workflow.workflow import isascii

FILTERS_MAP = {
    'key': 'key',
    'title': ['data', 'title'],
    'creators': ['creators', 'family'],
    'collection_title': [
        ['data', 'publicationTitle'],
        ['data', 'bookTitle'],
        ['data', 'proceedingsTitle']
    ],
    'date': ['data', 'date'],
    'collections': ['zot-collections', 'name'],
    'tags': ['zot-tags', 'name'],
    'attachments': ['attachments', 'name'],
    'notes': 'notes'  
}

FILTERS = {
    'general': [
        'key', 'title', 'creators', 'collection_title',
        'date', 'tags', 'collections', 'attachments', 'notes'
    ], 
    'titles': [
        'key', 'title', 'collection_title', 'date'
    ], 
    'creators': [
        'key', 'creators', 'date'
    ],
    'attachments': [
        'key', 'attachments'
    ], 
    'notes': [
        'key', 'notes'
    ],
    'tag': [
        'key', 'tags'
    ], 
    'collection': [
        'key', 'collections'
    ]
}

EXTS = ['pdf', 'epub', 'json']

def main(wf):

    print wf.stored_data('output_settings')

    

    


if __name__ == '__main__':
    WF = Workflow()
    fold = WF.fold_to_ascii
    sys.exit(WF.run(main))
