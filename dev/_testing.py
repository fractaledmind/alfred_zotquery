#!/usr/bin/python
# encoding: utf-8
import sys
from workflow import Workflow
import zot_helpers as zot
import json


def main(wf):
    lib = zot.json_read(wf.datafile('zotero_db.json'))
    new_dict = {}
    for item in lib:
        d = {item['key']: item}
        new_dict.update(d)
    
    zot.json_write(new_dict, wf.datafile('zotero_dict.json'))
    






if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
