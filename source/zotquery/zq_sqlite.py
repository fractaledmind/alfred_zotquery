#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import os


class ClonedSQlite(object):

    def __init__(self):
        self.path = WF.datafile('zotquery.sqlite')
        self.zotero = zot(WF)


if __name__ == '__main__':

    # add path to module root to `$PATH`
    root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, root)
    from workflow import Workflow
    from zotero import zot
    WF = Workflow()

    c = ClonedSQlite()
    print(os.path.exists(c.path))

