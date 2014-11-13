#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 19-08-2014
#
from __future__ import unicode_literals

# Standard Library
import re
import json
import os.path
import functools

# Internal Dependencies
from lib import utils
from workflow import Workflow, PasswordNotFound

WF = Workflow()
log = WF.logger
decode = WF.decode

__version__ = '10.0'

__usage__ = """
ZotQuery -- An Alfred GUI for `zotero`

Usage:
    zotquery.py configure <flag> [<argument>]
    zotquery.py search <flag> [<argument>]
    zotquery.py store <flag> <argument>
    zotquery.py export <flag> <argument>
    zotquery.py append <flag> <argument>
    zotquery.py open <flag> <argument>
    zotquery.py scan <flag> [<argument>]

Arguments:
    <flag>      Determines which specific code-path to follow
    <argument>  The value to be stored, searched, or passed on
"""


# -----------------------------------------------------------------------------
# WORKFLOW USAGE PREFERENCES
# Feel free to change
# -----------------------------------------------------------------------------

# What is copied to the clipboard with `cmd+c`?
def quick_copy(item):
    """Generate `str` for QUICK_COPY.
    Example: {@lastname_1900_XYZ}

    """
    # Get YEAR var
    try:
        year = item['data']['date']
    except KeyError:
        year = 'yyyy'
    # Get and format CREATOR var
    if len(item['creators']) == 0:
        last = 'xxx'
    elif len(item['creators']) == 1:
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
    scannable_str = '_'.join([last, year, item['key'][-3:]])
    return '{@' + scannable_str + '}'

# Can be [1] a `key` from FILTERS_MAP (so a `str`)
# OR [2] a user-made function to generate a `str`
# that takes the dictionary of `item` as its argument
# This takes option [2].
QUICK_COPY = quick_copy
#QUICK_COPY = 'key'  # OR 'title'


# What is shown in Alfred's large text with `cmd+l`?
def large_text(item):
    """Get large text"""
    large = str()
    try:
        large = '\n'.join(item['notes'])
    except KeyError:
        pass
    try:
        large = item['data']['abstractNote']
    except KeyError:
        pass
    try:
        large_text = decode(large)
    except TypeError:
        large_text = str(large)
    return re.sub(r'\r|\n', ' ', large_text)

# Same as above: [1] or [2]
LARGE_TEXT = large_text

# Only save and search items from your Personal Zotero library?
PERSONAL_ONLY = False

# Cache formatted references for faster re-retrieval?
CACHE_REFERENCES = True

# Allow ZotQuery to learn which items are used more frequently?
ALFRED_LEARN = False

# Accepted extensions for ZotQuery attachments
ATTACH_EXTS = [
    'pdf',
    'doc',
    'docx',
    'epub'
]

# -----------------------------------------------------------------------------
# WORKFLOW USAGE SETTINGS
# These are dangerous to change
# -----------------------------------------------------------------------------

# Map of search columns (`key`) to JSON location (`value`)
FILTERS_MAP = {
    'key': 'key',
    'title': ['data', 'title'],
    'creators': ['creators', 'family'],
    'collection_title': [
        ['data', 'publicationTitle'],
        ['data', 'bookTitle'],
        ['data', 'proceedingsTitle']
    ],
    'date': ['data', 'date'],
    'collections': ['zot-collections', 'name'],
    'tags': ['zot-tags', 'name'],
    'attachments': ['attachments', 'name'],
    'notes': 'notes'
}

# Map of search filters (`key`) to search columns (`value`)
FILTERS = {
    'general': [
        'key', 'title', 'creators', 'collection_title',
        'date', 'tags', 'collections', 'attachments', 'notes'
    ],
    'titles': [
        'key', 'title', 'collection_title', 'date'
    ],
    'creators': [
        'key', 'creators', 'date'
    ],
    'attachments': [
        'key', 'attachments'
    ],
    'notes': [
        'key', 'notes'
    ],
    'tag': [
        'key', 'tags'
    ],
    'collection': [
        'key', 'collections'
    ]
}

# Map of search types (`key`) to search filters (`value`)
SCOPE_TYPES = {
    'items': ['general', 'titles', 'creators', 'attachments', 'notes'],
    'groups': ['collections', 'tags'],
    'in-groups': ['in-collection', 'in-tag'],
    'meta': ['debug', 'new']
}

# Path to `pashua` housed in bundler directory
PASHUA = os.path.join(WF.workflowfile('zotquery/lib/Pashua.app'),
                      'Contents/MacOS/Pashua')


# -----------------------------------------------------------------------------
# WORKFLOW Classes and Functions
# -----------------------------------------------------------------------------


class PropertyBase(object):
    def __init__(self, wf, secured=False):
        self.wf = wf
        # store properties dict in Keychain (True) or to file (False)
        self.secured = secured
         # get name of class in underscore format
        self.class_name = utils.convert(self.__class__.__name__)
        # ensure all sub-class properties are written to disk
        self.properties = self._properties(secured)

    def _properties(self, secured):
        if secured:
            return self.secure()
        else:
            return self.unsecure()

    def unsecure(self):
        """Will store properties dictionary in workflow's storage dir.

        """
        def getter():
            # look for file in workflow's storage dir
            return self.wf.stored_data(self.class_name)

        def setter(properties):
            # save that dictionary to disk in JSON format
            self.wf.store_data(self.class_name, properties,
                               serializer='json')
            return True

        return self.get_properties(getter, setter)

    def secure(self):
        """Just like `unsecure()`, but uses the Keychain."""
        def getter():
            pw = self.check_password(self.class_name)
            try:
                return json.loads(pw)
            except TypeError:
                return pw
            except ValueError:
                return pw

        def setter(properties):
            json_str = json.dumps(properties)
            self.wf.save_password(self.class_name, json_str)

        return self.get_properties(getter, setter)

    def get_properties(self, getter, setter):
        """Base class method to auto-generate and auto-update a JSON file
        with a dictionary of the sub-class's properties and values.

        Will store properties dictionary in workflow's storage dir.

        If any property is `null`, will try to re-generate it (in case
        it has been updated on the system).

        Use in conjunction with `stored_property` decorator.

        """
        # get properties
        properties = getter()
        if not properties:
            # get names of all properties of this class
            prop_names = [k for (k, v) in self.__class__.__dict__.items()
                          if isinstance(v, property)]
            properties = dict()
            for prop in prop_names:
                # generate dictionary of property names and values
                properties[prop] = getattr(self, prop)
        # if any property has a null value
        elif None in properties.values():
                # get names of any null properties
                null_props = [k for k, v in properties.items()
                              if not v]
                for prop in null_props:
                    # update null property
                    properties[prop] = getattr(self, prop)
        # if all properties already set
        else:
            return properties
        # store generated dictionary in JSON format
        setter(properties)
        # return data generated in situ
        return properties

    def check_password(self, account, setter=False):
        """Try to retrieve the password saved at ``account``.
        Return empty string if no password found.

        """
        try:
            return self.wf.get_password(account)
        except PasswordNotFound:
            if setter:
                setter()
                return self.check_password(account)
            else:
                return ''

    def check_storage(self, name, setter=False):
        settings = self.wf.cached_data('output_settings', max_age=0)
        try:
            return settings[name]
        except (KeyError, TypeError):
            if setter:
                setter()
                return self.check_storage(name)
            else:
                return ''


# DECORATORS  -----------------------------------------------------------------

def stored_property(func):
    """This ``decorator`` adds on-disk functionality to the `property`
    decorator. This decorator is also a Method Decorator.

    Each key property of a class is stored in a settings JSON file with
    a dictionary of property names and values (e.g. :class:`MyClass`
    stores its properties in `my_class.json`). To use this decorator on
    some class's properties, that class needs to be a sub-class of
    :class:`PropertyBase`.

    Take, for example, a simple class with a couple of properties like so:
    ```
    class MyClass(PropertyBase):
        def __init__(self, wf):
            self.wf = wf
            PropertyBase.__init__(self, self.wf)

        @stored_property
        def first_property(self):
            # some code to get data
            return 'this is my first property'

        @stored_property
        def second_property(self):
            import time
            time.sleep(2)
            return 'this is my second property'
    ```

    This will generate a JSON dictionary:
    ```
    {
      "first_property": "this is my first property",
      "second_property": "this is my second property"
    }
    ```

    """
    @property
    @functools.wraps(func)
    def func_wrapper(self):
        try:
            var = self.properties[func.__name__]
            if var:
                # property already written to disk
                return var
            else:
                # property written to disk as `null`
                return func(self)
        except AttributeError:
            # `self.me` does not yet exist
            return func(self)
        except KeyError:
            # `self.me` exists, but property is not a key
            return func(self)
    return func_wrapper

