#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import sys
from workflow import Workflow
from utils import json_read
from lib import bundler

bundler.init()
from pyzotero import zotero

def unify(text, encoding='utf-8'):
    """Convert `text` to unicode"""

    # https://github.com/kumar303/unicode-in-python/blob/master/unicode.txt
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return text

def _scan_cites(zot_data, item_key):
    """Exports ODT-RTF styled Scannable Cite"""

    for item in zot_data.values():
        if item['key'] == item_key:
            # Get YEAR var
            year = item['data']['date']
            # Get and format CREATOR var
            if len(item['creators']) == 1:
                last = item['creators'][0]['family']
            elif len(item['creators']) == 2:
                last1 = item['creators'][0]['family']
                last2 = item['creators'][1]['family']
                last = last1 + ', & ' + last2
            elif len(item['creators']) > 2:
                for i in item['creators']:
                    if i['type'] == 'author':
                        last = i['family'] + ', et al.'
                try:
                    last
                except NameError:
                    last = item['creators'][0]['family'] + ', et al.'
            break

    scannable_str = '_'.join([last, year, item_key[-3:]])
    scannable_cite = '{@' + scannable_str + '}'
    return unify(scannable_cite)

def parse_cite(zot_data, citekey):
    """NN"""
    id_partial = citekey.split('_')[-1]
    if id_partial.endswith('}'):
        id_partial = id_partial[:-1]

    for item in zot_data.keys():
        if item[-3:] == id_partial:
            item_key = item
            break

    zot = zotero.Zotero('1140739', 
                        'user', 
                        'rf8L5AZdrVlK9NMTXDVuotok')
    ref = zot.item(item_key, content='bib', style='chicago-author-date')
    return ref


def main(wf_obj):
    """Accept Alfred's args and pipe to proper Class"""
    key = "3KFT2HQ9"
    data = json_read(wf_obj.datafile("zotquery.json"))
    cited = _scan_cites(data, key)
    cite_id = parse_cite(data, cited)
    print cited
    print cite_id
    

if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
