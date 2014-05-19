#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import json
import os.path
import subprocess
from StringIO import StringIO

from deps import xmltodict
import zotquery as z

os.environ['__CF_USER_TEXT_ENCODING'] = "0x1F5:0x8000100:0x8000100"

def to_unicode(obj, encoding='utf-8'):
    """Detects if object is a string and if so converts to unicode"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def get_clipboard(): 
    """Get objects of clipboard"""
    scpt = """return the clipboard"""
    data = subprocess.call(['osascript', '-e', scpt])
    data = to_unicode(data)
    return data

def capture_output(zot_filter):
    """Capture `sys` output in var"""
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    zot_filter.filter()
    sys.stdout = old_stdout
    res_dict = xmltodict.parse(mystdout.getvalue())
    return res_dict

def main():
    """main"""
    proc = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    proc.wait()
    data = proc.stdout.read()

    for i in ['utf-8', 'cp1252']:
        try:
            print data.decode(i)
            print i
        except:
            pass

    
if __name__ == '__main__':
    main()
