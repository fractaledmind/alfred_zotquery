#!/usr/bin/python
# encoding: utf-8
from __future__ import print_function, unicode_literals


import sys
import os
from StringIO import StringIO
import unittest
import json
import tempfile
import shutil
import logging
import time
from xml.etree import ElementTree as ET
from unicodedata import normalize

from actions import search
import config


def setUp():
    pass


def tearDown():
    pass


class SearchTests(unittest.TestCase):
    """Test workflow.manager serialisation API"""

    def setUp(self):
        self.searches = (
            ('general', 'margheim'),
            ('titles', 'epistem'),
            ('creators', 'noël'),
            ('attachments', 'epicurus'),
            ('notes', 'horace'),
            ('tag', 'math'),
            ('collection', 'epi'),
            #('invalid', 'false')
        )
        self.searcher = search.SearchItem

    def tearDown(self):
        pass

    def test_query_maker(self):

        def test_scope_to_columns(maker, args):
            gen_columns = maker.scope_to_columns(args[0])
            got_columns = config.FILTERS.get(args[0])
            print(config.FILTERS.get(args[0]))
            self.assertEqual(gen_columns, got_columns)

        for args in self.searches:
            searcher = self.searcher(args[0], args[1])
            maker = searcher.SqliteQueryMaker(args[0], args[1])
            test_scope_to_columns(maker, args)


    

if __name__ == '__main__':  # pragma: no cover
    unittest.main()