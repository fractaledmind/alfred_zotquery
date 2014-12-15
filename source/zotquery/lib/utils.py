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
import unicodedata
import subprocess
import traceback
import codecs
import json
import sys
import os
import re


def full_stack():
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if not exc is None:  # i.e. if an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if not exc is None:
        stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr


def check_value(value):
    if value:
        return value
    else:
        return 'xxx.'


###########################################################################
# IO functions                                                            #
###########################################################################

def read_json(path, encoding='utf-8'):
    """Read JSON string from `path`."""
    if os.path.exists(path):
        with codecs.open(path, 'r', encoding=encoding) as file_obj:
            content = ''.join(file_obj.readlines())
            file_obj.close()
        if content != '':
            return json.loads(content)
        else:
            return None
    else:
        raise Exception("'{}' does not exist.".format(path))


def write_json(data, path):
    """Write `data` to `path` as formatted JSON string"""
    formatted_json = json.dumps(data,
                                sort_keys=False,
                                indent=4,
                                separators=(',', ': '))
    u_json = decode(formatted_json)
    with open(path, 'w') as file_obj:
        file_obj.write(u_json.encode('utf-8'))
        file_obj.close()
    return True


def read_path(path, encoding='utf-8'):
    """Read data from `path`"""
    if os.path.exists(path):
        with codecs.open(path, 'r', encoding=encoding) as file_obj:
            data = file_obj.read()
            file_obj.close()
        return decode(data)
    else:
        raise Exception("'{}' does not exist.".format(path))


def write_path(data, path):
    """Write Unicode `data` to `path`"""
    u_data = decode(data)
    with open(path, 'w') as file_obj:
        file_obj.write(u_data.encode('utf-8'))
        file_obj.close()
    return True


def append_path(data, path):
    """Write Unicode `data` to `path`"""
    u_data = decode(data)
    with open(path, 'a') as file_obj:
        file_obj.write(u_data.encode('utf-8'))
        file_obj.close()
    return True


###########################################################################
# Type conversion functions                                               #
###########################################################################

def decode(text, encoding='utf-8', normalization='NFC'):
    """Convert `text` to unicode"""
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return unicodedata.normalize(normalization, text)


def to_bool(text):
    """Convert string to Boolean"""
    if str(text).lower() in ('true', 't', '1'):
        return True
    elif str(text).lower() in ('false', 'f', '0'):
        return False


def strip(obj):
    try:
        return obj.strip()
    except AttributeError:
        return obj


###########################################################################
# Clipboard functions                                                     #
###########################################################################

def set_clipboard(data):
    """Set clipboard to `data`"""
    os.environ['LANG'] = 'en_US.UTF-8'
    text = decode(data)
    proc = subprocess.Popen(['pbcopy', 'w'], stdin=subprocess.PIPE)
    proc.communicate(input=text.encode('utf-8'))


def get_clipboard():
    """Retrieve data from clipboard"""
    os.environ['LANG'] = 'en_US.UTF-8'
    proc = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    return decode(stdout)


###########################################################################
# Applescript functions                                                   #
###########################################################################

def run_filter(trigger, arg):
    """Run Alfred filter."""
    trigger = applescriptify_str(trigger)
    arg = applescriptify_str(arg)
    scpt = """tell application "Alfred 2"
              to run trigger "{}"
              in workflow "com.hackademic.zotquery"
              with argument "{}"
           """.format(trigger, arg)
    run_applescript(scpt)


def run_alfred(query):
    """Run Alfred with `query` via AppleScript."""
    alfred_scpt = 'tell application "Alfred 2" to search "{}"'
    script = alfred_scpt.format(applescriptify_str(query))
    return subprocess.call(['osascript', '-e', script])


###########################################################################
# Conversion functions                                                    #
###########################################################################

def convert(camel_case):
    """Convert CamelCase to underscore_format."""
    camel_re = re.compile(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
    return camel_re.sub(r'_\1', camel_case).lower()


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
