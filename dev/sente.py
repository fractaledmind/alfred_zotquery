#!/usr/bin/python
# encoding: utf-8

from __future__ import unicode_literals
import re
import json
#import sqlite3
import os.path
import subprocess
from collections import OrderedDict

# Hard code the path to the Sente Database
BASE = os.path.join(os.path.expanduser("~"), "Desktop/JSON")
DATABASE = BASE + "/Sources.sente6lib/Contents/primaryLibrary.sente601"
# You need to use Sente's internal `sqlite3` executable.
# For some reason, the basic Python module will fail on certain queries
SQLITE = "/Applications/Sente 6.app/Contents/MacOS/sqlite3"

# List of relevant item info columns
NAMES = [
    "Citation",
    "publicationType",
    "publicationTitle",
    "volume",
    "issue",
    "pages",
    "articleTitle",
    "abstractText",
    "publicationYear",
    "AttachmentCount"
]

def _unify(text, encoding='utf-8'):
    """Detects if ``text`` is a string and if so converts to unicode"""
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return text

FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP = re.compile('([a-z0-9])([A-Z])')
def convert(name):
    """Convert CamelCase to camel_case"""
    initial = FIRST_CAP.sub(r'\1_\2', name)
    return ALL_CAP.sub(r'\1_\2', initial).lower()

def run_sql(_sql):
    """Run passed SQL query thru Sente's internal `sqlite3` executable"""
    # This will be the way in which you execute sqlite queries without
    # using Python's `sqlite3` module. It will ensure good results with Sente
    _pipe = subprocess.Popen([SQLITE, DATABASE, _sql], stdout=subprocess.PIPE)
    return _unify(_pipe.communicate()[0]).strip()

def main():

    # Get all items' ID
    _sql = """SELECT ReferenceUUID
    FROM ReferenceSignature"""
    _pipe = run_sql(_sql)
    ids = _pipe.split('\n') # You need to turn the `str` into a `list`

    # It's best to work with one Sente item at a time
    _items = []
    for item in ids:
        # prepare item's base dict and data dict
        item_dict = OrderedDict()
        item_meta = OrderedDict()

        item_dict['id'] = item

        ### Creator data query
        item_dict['creators'] = []
        _creators = """SELECT LastName, ForeNames, Role, SequenceNumber
        FROM Author
        WHERE ReferenceUUID = '{0}'""".format(item)
        # Get creator data, convert to Unicode (returns string)
        creators_str = run_sql(_creators)
        # Convert creator data string to nested list
        # e.g. [[Last1, First1, Type1, Num1], [Last2, First2, Type2, Num2]]
        # The `creators_str.strip().split('\n')` creates list of all author data
        # e.g. ['Last1|First1|Type1|Num1', 'Last2|First2|Type2|Num2']
        # The second part of the list comprehension creates sub-list of data
        creators_lst = [x.split('|') for x in creators_str.strip().split('\n')]
        for creator in creators_lst:
            first_name = last_name = c_type = order_index = ''
            try:
                (last_name, 
                first_name, 
                c_type,
                order_index) = creator
            except ValueError: # empty value
                pass
            item_dict['creators'].append({'family': last_name, 
                                          'given': first_name, 
                                          'type': c_type, 
                                          'index': order_index})
        # Get meta data for item
        for name in NAMES:
            # Get value of relevant meta data fields
            _data = """SELECT {1}
            FROM Reference
            WHERE ReferenceUUID = '{0}'""".format(item, name)
            data_str = run_sql(_data)
            if data_str != "": # only capture non-null fields
                if name == "publicationType": # item type
                    item_dict['type'] = data_str
                else:
                    field = convert(name)
                    item_meta[field] = data_str

        # Sub-nest meta data
        item_dict['data'] = item_meta

        # Append `dict` to list of all items
        _items.append(item_dict)

    # Convert list of dicts to JSON
    final_json = json.dumps(_items, 
                            sort_keys=False, 
                            indent=4, 
                            separators=(',', ': '))
    print final_json


if __name__ == '__main__':
    main()
