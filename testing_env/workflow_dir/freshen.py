#!/usr/bin/python
# encoding: utf-8
import sys
import sqlite3
import os.path
from shutil import copyfile
from zotquery import Zotero, ZotQuery
from workflow import Workflow

def update_clone(wf, zotero):
    """Update `cloned_sqlite` so that it's current with `original_sqlite`.

    """
    clone_path = wf.datafile("zotquery.sqlite")
    copyfile(zotero.original_sqlite, clone_path)
    log.info('Updated Clone SQLITE file')

def update_json(wf, zotquery):
    """Update `json_data` so that it's current with `cloned_sqlite`.

    """
    con = sqlite3.connect(zotquery.cloned_sqlite)
    # backup previous version of library
    if os.path.exists(zotquery.json_data):
        copyfile(zotquery.json_data, wf.datafile('backup.json'))
    # update library
    zotquery.to_json()
    log.info('Updated and backed-up JSON file')

def main(wf):
    """Refresh ZotQuery data stores"""

    args = wf.args
    zotero = Zotero(wf)
    zotquery = ZotQuery(wf)
    if args[0] == 'True':
    	update_clone(wf, zotero)
    	update_json(wf, zotquery)
    elif args[0] == 'False':
    	update, spot = zotquery.is_fresh()
        if update == True:
            if spot == 'Clone':
                zotquery.update_clone()
            elif spot == 'JSON':
                zotquery.update_json()


if __name__ == '__main__':
    WF = Workflow()
    log = WF.logger
    sys.exit(WF.run(main))
