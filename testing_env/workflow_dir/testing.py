#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import sys
from lib import bundler
bundler.init()
from pyzotero import zotero3 as zotero

#md = '/Users/smargheim/Documents/DEVELOPMENT/GitHub/pandoc-templates/examples/academic_test.txt'
#args = ['scan', md, 'Moritz_1969']

zot = zotero.Zotero('1140739', 
                    'user', 
                    'rf8L5AZdrVlK9NMTXDVuotok')

print zot.items(tag='Mathematics',
              content='bib',
              style='apa')