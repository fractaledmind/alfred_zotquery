#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import os.path
from workflow import Workflow

BASE = os.path.expanduser(
    '~/Library/Application Support/Alfred 2/Workflow Data/')
BUNDLER = "alfred.bundler-aries/assets/python"
PATH = os.path.join(BASE, BUNDLER)








def main(wf_obj):
    """main"""
    WF_DIR = os.path.dirname(os.path.realpath(__file__))
    PLIST = os.path.join(WF_DIR, 'info.plist')
    print os.path.exists(PLIST)


    

    
if __name__ == '__main__':
    WF = Workflow(libraries=[PATH])
    sys.exit(WF.run(main))
