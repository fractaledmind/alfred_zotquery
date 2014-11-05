#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 17-05-2014
#
from __future__ import unicode_literals

# Standard Library
import subprocess
import codecs
import json
import os


###########################################################################
# IO functions                                                            #
###########################################################################

def json_read(path, encoding='utf-8'):
    """Read JSON string from `path`.

    """

    if os.path.exists(path):
        with codecs.open(path, 'r', encoding=encoding) as file_obj:
            content = ''.join(file_obj.readlines())
            file_obj.close()
        if content != '':
            return json.loads(content)
        else:
            return None
    else:
        open(path, 'w')
        return None

def json_write(data, path):
    """Write `data` to `path` as formatted JSON string"""

    formatted_json = json.dumps(data, 
                                sort_keys=False, 
                                indent=4, 
                                separators=(',', ': '))
    u_json = to_unicode(formatted_json)
    with open(path, 'w') as file_obj:
        file_obj.write(u_json.encode('utf-8'))
        file_obj.close()
    return True

def path_read(path, encoding='utf-8'):
    """Read data from `path`"""

    if os.path.exists(path):
        with codecs.open(path, 'r', encoding=encoding) as file_obj:
            data = file_obj.read()
            file_obj.close()
        return to_unicode(data)
    else:
        raise Exception("'{}' does not exist.".format(path))

def path_write(data, path):
    """Write Unicode `data` to `path`"""

    u_data = to_unicode(data)
    with open(path, 'w') as file_obj:
        file_obj.write(u_data.encode('utf-8'))
        file_obj.close()
    return True

###########################################################################
# Type conversion functions                                               #
###########################################################################

def to_unicode(text, encoding='utf-8'):
    """Convert `text` to unicode"""

    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return text

def to_bool(text):
    """Convert string to Boolean"""

    if str(text).lower() in ('true', 't', '1'):
        return True
    elif str(text).lower() in ('false', 'f', '0'):
        return False

###########################################################################
# Clipboard functions                                                     #
###########################################################################

def set_clipboard(data):
    """Set clipboard to `data`"""

    os.environ['__CF_USER_TEXT_ENCODING'] = "0x1F5:0x8000100:0x8000100"
    text = to_unicode(data)
    proc = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE)
    proc.communicate(input=text.encode('utf-8'))

def get_clipboard():
    """Retrieve data from clipboard"""

    os.environ['__CF_USER_TEXT_ENCODING'] = "0x1F5:0x8000100:0x8000100"
    proc = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    return to_unicode(stdout)

###########################################################################
# Applescript functions                                                   #
###########################################################################

def run_filter(trigger, arg):
    """Run Alfred filter.
    """
    trigger = applescriptify(trigger)
    arg = applescriptify(arg)
    scpt = """tell application "Alfred 2" \
            to run trigger "{}" \
            in workflow "com.hackademic.zotquery" \
            with argument "{}"
        """.format(trigger, arg)
    run_applescript(scpt)

def run_alfred(query):
    """Run Alfred with `query` via AppleScript.
    """
    alfred_scpt = 'tell application "Alfred 2" to search "{}"'
    script = alfred_scpt.format(applescriptify(query))
    return subprocess.call(['osascript', '-e', script])

def applescriptify(text):
    """Replace double quotes in `text` for Applescript"""

    return to_unicode(text).replace('"', '" & quote & "')

def run_applescript(scpt_str):
    """Run an applescript"""

    proc = subprocess.Popen(['osascript', '-e', scpt_str],
                                stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    return to_unicode(out.strip())

###########################################################################
# Conversion functions                                                    #
###########################################################################

def html2rtf(html_path):
    """Convert html to RTF and copy to clipboard"""

    textutil = subprocess.Popen(
        ["textutil", "-convert", "rtf", html_path, '-stdout'],
        stdout=subprocess.PIPE)
    copy = subprocess.Popen(
        ["pbcopy"],
        stdin=textutil.stdout)

    textutil.stdout.close()
    copy.communicate()
    return True

