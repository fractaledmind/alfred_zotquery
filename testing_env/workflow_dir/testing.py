#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import sys
from workflow.background import run_in_background
from workflow import Workflow

def pashua(**kwargs):
    for name, ui in kwargs['interface'].items():
        for key, val in ui.items():
            if key == 'options':
                for opt in ui['options']:
                    print name + '.option = ' + opt
            else:
                print name + '.' + key + ' = ' + val

pashua(title='ZotQuery',
       interface={
           'app': {
                'type': 'radiobutton',
                'options': [
                    'Standalone',
                    'Firefox'
                ],
                'default': 'Standalone'
            },
            'csl': {
                'type': 'radiobutton',
                'label': 'Select',
                'options': [
                    'chicago',
                    'apa',
                    'mla',
                    'bibtex'
                ]
            }
        }
    )