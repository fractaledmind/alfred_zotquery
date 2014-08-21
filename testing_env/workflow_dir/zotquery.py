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
import os
import re
import sys
import struct
import sqlite3
import os.path
import subprocess
from time import time
from shutil import copyfile
from collections import OrderedDict

# Internal Dependencies
import utils
from lib import pashua, bundler, html2text
from lib.docopt import docopt

# Alfred-Workflow
from workflow import Workflow, web, ICON_WARNING, PasswordNotFound
from workflow.workflow import isascii, split_on_delimiters


__version__ = '10.0'

__usage__ = """
ZotQuery -- An Alfred GUI for `zotero`

Usage:
    zotquery.py config <flag> [<argument>]
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

# ------------------------------------------------------------------------------
# WORKFLOW USAGE PREFERENCES 
# Feel free to change
# ------------------------------------------------------------------------------

# What is copied to the clipboard with `cmd+c`?
# Can be [1] a `key` from FILTERS_MAP (so a `str`)
# OR [2] a user-made function to generate a `str`
#that takes the dictionary of `item` as its argument
def quick_copy(item):
    """Generate `str` for QUICK_COPY"""
    # Get YEAR var
    try:
        year = item['data']['date']
    except KeyError:
        year = 'xxxx'
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
QUICK_COPY = quick_copy
#QUICK_COPY = 'key'
# What is shown in Alfred's large text with `cmd+l`?
# Same as above [1] or [2]
def large_text(item):
    """Get large text"""
    large = ''
    try:
        large = '\n'.join(item['notes'])
    except KeyError:
        pass
    try:
        large = item['data']['abstractNote']
    except KeyError:
        pass
    return re.sub(r"\r|\n", ' ', large)
LARGE_TEXT = large_text
# Only save items from your Personal Zotero library?
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

# ------------------------------------------------------------------------------
# WORKFLOW USAGE SETTINGS 
# These are dangerous to change
# ------------------------------------------------------------------------------

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
    'in-groups': ['in-collection', 'in-tag', 'new'],
    'meta': ['debug']
}
# Path to `pashua` housed in bundler directory
PASHUA = bundler.utility('pashua')
# `Workflow()` methods to be populated later
log = None
decode = None
fold = None

#-------------------------------------------------------------------------------
# :class:`Zotero` --------------------------------------------------------------
#-------------------------------------------------------------------------------

class Zotero(object):
    """Contains all relevant information about user's Zotero installation.

    :param wf: a new :class:`Workflow` instance.
    :type wf: :class:`object`

    """
    def __init__(self, wf):
        self.wf = wf
        self.me = self.paths()

    # `self.me` setter method --------------------------------------------------

    def paths(self):
        """Dictionary of paths to relevant Zotero data:
            ==================      ============================================
            Key                     Description
            ==================      ============================================
            `original_sqlite`       Zotero's internal sqlite database
            `internal_storage`      Zotero's internal storage directory
            `external_storage`      Zotero's external directory for attachments

        Expects information to be stored in :file:`zotero_paths.json`.
        If file does not exist, it creates and stores dictionary.

        :returns: key Zotero paths
        :rtype: :class:`dict`

        """
        zotero_paths = self.wf.stored_data('zotero_paths')
        if zotero_paths == None:
            paths = {
                'original_sqlite': self.original_sqlite,
                'internal_storage': self.internal_storage,
                'external_storage': self.external_storage
            }
            self.wf.store_data('zotero_paths', paths,
                                    serializer='json')
            zotero_paths = paths
        return zotero_paths

    # Zotero API setter method -------------------------------------------------

    def set_api(self):
        """Configure Zotero API data.

        """
        # Check if values have already been set
        try:
            api = self.wf.get_password('zotero_api')
        except PasswordNotFound:
            api = ''
        try:
            uid = self.wf.get_password('zotero_user')
        except PasswordNotFound:
            uid = ''
        # Prepare `pashua` config string
        conf = """
            # Set window title
            *.title = Zotero API Settings
            # Add API Key text field
            api.type = textfield
            api.label = Enter your Zotero API Key
            api.default = {api}
            api.width = 310
            # Add User ID text field
            id.type = textfield
            id.label = Enter your Zotero User ID
            id.default = {uid}
            id.width = 310
            # Add a cancel button with default label
            cb.type=cancelbutton
        """.format(api=api, uid=uid)
        # Run `pashua` dialog and save results to Keychain
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=PASHUA)
        if res_dict['cb'] != 1:
            self.wf.save_password('zotero_api', res_dict['api'])
            self.wf.save_password('zotero_user', res_dict['id'])

    # Zotero API getter property -----------------------------------------------

    @property
    def api_settings(self):
        """Retrieve user's Keychain stored Zotero API settings.

        :returns: all Zotero API data
        :rtype: :class:`dict`

        """
        api_key = self.wf.get_password('zotero_api')
        user_id = self.wf.get_password('zotero_user')
        user_type = 'user'
        return {
            'api_key': api_key,
            'user_id': user_id,
            'user_type': user_type
        }

    # `self.me` sub-properties -------------------------------------------------

    @property
    def original_sqlite(self):
        """Return path to Zotero's internal sqlite database.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.me['original_sqlite']
        except AttributeError:
            sqlites = self.find_name('zotero.sqlite')
            return sqlites[0] if sqlites != [] else None

    @property
    def internal_storage(self):
        """Return path to Zotero's internal storage directory for attachments.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to directory
        :rtype: :class:`unicode`

        """
        try:
            return self.me['internal_storage']
        except AttributeError:
            zotero_dir = os.path.dirname(self.original_sqlite)
            storage_dir = os.path.join(zotero_dir, 'storage')
            if os.path.exists(storage_dir):
                return storage_dir
            else:
                for name in ('dataDir', 'lastDataDir'):
                    dir_pref = self.get_pref(name)
                    if dir_pref != None:
                        return dir_pref

    @property
    def external_storage(self):
        """Return path to Zotero's external storage directory for attachments.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to directory
        :rtype: :class:`unicode`

        """
        try:
            return self.me['external_storage']
        except AttributeError:
            return self.get_pref('baseAttachmentPath')

    # `self.zotero` utility methods --------------------------------------------

    def get_pref(self, pref):
        """Retrieve the value for ``pref`` in Zotero's preferences.

        :param pref: name of desired Zotero preference
        :type pref: :class:`unicode` or :class:`str`
        :returns: Zotero preference value
        :rtype: :class:`unicode`

        """
        dirs = self.find_name('prefs.js')
        for path in dirs:
            prefs = utils.path_read(path)
            pref_re = r'{}",\s"(.*?)"'.format(pref)
            data_dir = re.search(pref_re, prefs)
            try:
                return data_dir.group(1)
            except AttributeError:
                pass
        return None

    @staticmethod
    def find_name(name):
        """Use `mdfind` to locate file given its ``name``.

        :param name: full name of desired file
        :type name: :class:`unicode` or :class:`str`
        :returns: list of paths to named file
        :rtype: :class:`list`

        """
        cmd = ['mdfind',
               'kMDItemFSName={}'.format(name)]
        output = subprocess.check_output(cmd)
        output = [s.strip() for s in decode(output).split('\n')]
        return filter(None, output)

#-------------------------------------------------------------------------------
# :class:`ZotQuery` ------------------------------------------------------------
#-------------------------------------------------------------------------------

class ZotQuery(object):
    """Contains all relevant information about this workflow.

    :param wf: a new :class:`Workflow` instance.
    :type wf: :class:`object`

    """
    def __init__(self, wf):
        self.wf = wf
        self.zotero = Zotero(self.wf)
        self.con = None
        self.me = self.paths()

    # `self.me` setter method --------------------------------------------------

    def paths(self):
        """Dictionary of paths to relevant ZotQuery data:
            ==================      ============================================
            Key                     Description
            ==================      ============================================
            `cloned_sqlite`         ZotQuery's clone of Zotero's sqlite database
            `json_data`             ZotQuery's JSON clone of Zotero's sqlite
            `fts_sqlite`            ZotQuery's Full Text Search database
            `folded_sqlite`         ZotQuery's ASCII-only FTS database

        Expects information to be stored in data file ``zotquery_paths.json``.
        If file does not exist, :prop:`paths` creates and stores dictionary.

        :returns: key ZotQuery paths
        :rtype: :class:`dict`

        """
        zotquery = self.wf.stored_data('zotquery_paths')
        if zotquery == None:
            paths = {
                'cloned_sqlite': self.cloned_sqlite,
                'json_data': self.json_data,
                'fts_sqlite': self.fts_sqlite,
                'folded_sqlite': self.folded_sqlite
            }
            self.wf.store_data('zotquery_paths', paths,
                                        serializer='json')
            zotquery = paths
        return zotquery

    # ZotQuery Formatting setter method ----------------------------------------

    def set_output(self):
        """Configure ZotQuery formatting perferences.

        """
        # Check if values have already been set
        defaults = self.output_settings
        if defaults == None:
            defaults = {'app': 'Standalone',
                        'csl': 'chicago-author-date',
                        'fmt': 'Markdown'}
        # Prepare `pashua` config string
        conf = """
        # Set window title
        *.title = ZotQuery Output Preferences
        # Define Zotero app
        app.type = radiobutton
        app.label = Select your Zotero application client:
        app.option = Standalone
        app.option = Firefox
        app.default = {app}
        # Define CSL style
        csl.type = radiobutton
        csl.label = Select your your desired CSL style:
        csl.option = chicago-author-date
        csl.option = apa
        csl.option = modern-language-association
        csl.option = rtf-scan
        csl.option = bibtex
        csl.option = odt-scannable-cites
        csl.default = {csl}
        # Define output format
        fmt.type = radiobutton
        fmt.label = Select your desired output format:
        fmt.option = Markdown
        fmt.option = Rich Text
        fmt.default = {fmt}
        # Add a cancel button with default label
        cb.type=cancelbutton
        """.format(app=defaults['app'],
                   csl=defaults['csl'],
                   fmt=defaults['fmt'])
        # Run `pashua` dialog and save results to storage file
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=PASHUA)
        if res_dict['cb'] != 1:
            del res_dict['cb']
            self.wf.store_data('output_settings', res_dict, serializer='json')

    # ZotQuery Formatting getter property --------------------------------------

    @property
    def output_settings(self):
        """Retrieve user chosen output settings.

        :returns: formatting preferences
        :rtype: :class:`dict`

        """
        return self.wf.stored_data('output_settings')

    # `self.me` sub-properties -------------------------------------------------

    @property
    def cloned_sqlite(self):
        """Return path to ZotQuery's cloned sqlite database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it creates the file by cloning
        ``original_sqlite`` from :attr:`Zotero.paths`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.me['cloned_sqlite']
        except AttributeError:
            clone_path = self.wf.datafile("zotquery.sqlite")
            if not os.path.exists(clone_path):
                copyfile(self.zotero.original_sqlite, clone_path)
                log.info('Created Clone SQLITE file')
            return clone_path

    @property
    def json_data(self):
        """Return path to ZotQuery's JSON version of user's Zotero database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it generates the file with data
        from :attr:`ZotQuery.cloned_sqlite`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.me['json_data']
        except AttributeError:
            json_path = self.wf.datafile("zotquery.json")
            if not os.path.exists(json_path):
                self.con = sqlite3.connect(self.cloned_sqlite)
                self.to_json()
            return json_path

    @property
    def fts_sqlite(self):
        """Return path to ZotQuery's Full Text Search sqlite database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it creates the database then
        fills it with data from :attr:`ZotQuery.json_data`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.me['fts_sqlite']
        except AttributeError:
            fts_path = self.wf.datafile("zotquery.db")
            if not os.path.exists(fts_path):
                self.create_index_db(fts_path)
                self.update_index_db(fts_path)
            return fts_path

    @property
    def folded_sqlite(self):
        """Return path to ZotQuery's Full Text Search sqlite database
        where all text if ASCII only.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it creates the database then
        fills it with data from :attr:`ZotQuery.json_data`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.me['folded_sqlite']
        except AttributeError:
            folded_path = self.wf.datafile("folded.db")
            if not os.path.exists(folded_path):
                self.create_index_db(folded_path)
                self.update_index_db(folded_path, folded=True)
            return folded_path

    # `self.me` utility methods ------------------------------------------------

    def is_fresh(self):
        """Is ZotQuery up-to-date with Zotero?

        Two specific questions:
            + is ``cloned_sqlite`` parallel to :attr:`Zotero.original_sqlite`?
            + is ``json_data`` parallel to ``cloned_sqlite``?

        :returns: tuple with Boolean answer and rotten file
        :rtype: :class:`tuple`

        """
        (update, spot) = (False, None)
        zotero_mod = os.stat(self.zotero.original_sqlite)[8]
        clone_mod = os.stat(self.cloned_sqlite)[8]
        cache_mod = os.stat(self.json_data)[8]
        # Check if cloned sqlite database is up-to-date with `zotero` database
        if zotero_mod > clone_mod:
            update, spot = (True, "Clone")
        # Check if JSON cache is up-to-date with the cloned database
        elif (cache_mod - clone_mod) > 10:
            update, spot = (True, "JSON")
        if update:
            log.debug('Update {}? {}'.format(spot, update))
        return (update, spot)

    def update_clone(self):
        """Update `cloned_sqlite` so that it's current with `original_sqlite`.

        """
        clone_path = self.wf.datafile("zotquery.sqlite")
        copyfile(self.zotero.original_sqlite, clone_path)
        log.info('Updated Clone SQLITE file')

    def update_json(self):
        """Update `json_data` so that it's current with `cloned_sqlite`.

        """
        self.con = sqlite3.connect(self.cloned_sqlite)
        self.to_json()


    @staticmethod
    def create_index_db(db):
        """Create FTS virtual table with data from ``json_data``

        :param db: path to `.db` file
        :type db: :class:`unicode`

        """
        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            # get search columns from `general` scope
            columns = FILTERS.get('general', None)
            if columns:
                # convert list to string
                columns = ', '.join(columns)
                sql = """CREATE VIRTUAL TABLE zotquery
                         USING fts3({cols})""".format(cols=columns)
                cur.execute(sql)
                log.debug('Created FTS database: {}'.format(db))

    def to_json(self):
        """Convert Zotero's sqlite database to structured JSON.

        This file is a dictionary wherein each item's Zotero key
        is the dictionary key. The value for each item is itself a 
        dictionary with all of that item's information, organized
        under these sub-keys:
            key
            library
            type
            creators
            data
            zot-collections
            zot-tags
            attachments
            notes
        *Note:* singular sub-keys (key, library, type, data) have a
        ``string`` or a ``dictionary`` as their value; plural sub-keys
        (creators, zot-collections, zot-tags, attachments, notes) all
        have a ``list`` as their value. 

        Here's an example item:
        ```
        "C3KEUQJW": {
            "key": "C3KEUQJW",
            "library": "0",
            "type": "journalArticle",
            "creators": [
                {
                    "index": 0,
                    "given": "Stephen",
                    "type": "author",
                    "family": "Margheim"
                }
            ],
            "data": {
                "volume": "1",
                "issue": "1",
                "pages": "1-14",
                "publicationTitle": "A Sample Publication",
                "date": "2013",
                "title": "Test Item"
            },
            "zot-collections": [],
            "zot-tags": [],
            "attachments": [
                {
                    "path": "path/to/some/file/test_item.pdf",
                    "name": "test_item.pdf",
                    "key": "GTDIDHW4"
                }
            ],
            "notes": []
        }
        ```
        Adapted from: <https://github.com/pkeane/zotero_hacks>
        
        """
        start = time()
        all_items = {}
        info_sql = """
            SELECT key, itemID, itemTypeID, libraryID
            FROM items
            WHERE 
                itemTypeID not IN (1, 13, 14)
            ORDER BY dateAdded DESC
        """
        basic_info = self._execute(info_sql)
        # iterate thru every item
        for basic in basic_info:
            # prepare item's root dict and metadata dict
            item_dict = OrderedDict()
            # save item's basic ids to variables
            item_key = item_id = item_type_id = library_id = ''
            (item_key,
             item_id,
             item_type_id,
             library_id) = basic
            # If user only wants personal library
            if PERSONAL_ONLY == True and library_id != None:
                continue
            library_id = library_id if library_id != None else '0'
            # place key ids in item's root dict
            item_dict['key'] = item_key
            item_dict['library'] = library_id
            item_dict['type'] = self._item_type_name(item_type_id)
            # add list of dicts with each creator's info to root dict
            item_dict['creators'] = self._item_creators(item_id)
            # add list of dicts with item's metadata to root dict
            item_dict['data'] = self._item_metadata(item_id)
            # add list of dicts with item's collections to root dict
            item_dict['zot-collections'] = self._item_collections(item_id)
            # add list of dicts with item's tags to root dict
            item_dict['zot-tags'] = self._item_tags(item_id)
            # add list of dicts with item's attachments to root dict
            item_dict['attachments'] = self._item_attachments(item_id)
            # add list of dicts with item's notes to root dict
            item_dict['notes'] = self._item_notes(item_id)
            # add all data as value of `item_key`
            all_items[item_key] = item_dict
        self.con.close()
        self.wf.store_data('zotquery', all_items, serializer='json')
        log.info('Created JSON file in {:0.3} seconds'.format(time() - start))

    # JSON to FTS sub-methods --------------------------------------------------

    def update_index_db(self, fts_path, folded=False):
        """Update ``fts_sqlite`` with JSON data from ``json_data``.

        Reads in data from ``json_data`` and adds it to the FTS database.

        :param fts_path: path to `.db` file
        :type fts_path: :class:`unicode`
        :param folded: should all text be ASCII-normalized?
        :type folded: :class:`boolean`

        """
        # grab start time
        start = time()
        con = sqlite3.connect(fts_path)
        count = 0
        with con:
            cur = con.cursor()
            # iterate over every item in library
            for row in self.generate_data():
                columns = ', '.join([x.keys()[0] for x in row])
                values = ['"' + x.values()[0].replace('"', "'") + '"'
                            for x in row]
                values = ', '.join(values)
                # fold to ASCII-only?
                if folded != False:
                    values = fold(values)
                sql = """INSERT OR IGNORE INTO zotquery
                         ({columns}) VALUES ({data})
                        """.format(columns=columns, data=values)
                cur.execute(sql)
                count += 1
        log.debug('Added/Updated {} items in {:0.3} seconds'.format(count,
                                                                time() - start))

    def generate_data(self):
        """Create a genererator with dictionaries for each item
        in ``json_data``.

        :returns: ``list`` of ``dicts`` with all item's data as ``strings``
        :rtype: :class:`genererator`

        """
        json_data = utils.json_read(self.json_data)
        for item in json_data.itervalues():
            array = list()
            # get search columns from scope
            columns = FILTERS.get('general', None)
            if columns:
                for column in columns:
                    # get search map from column
                    json_map = FILTERS_MAP.get(column, None)
                    if json_map:
                        # get data from `item` using search map
                        array.append({column: self.get_datum(item, json_map)})
            yield array

    @staticmethod
    def get_datum(item, val_map):
        """Retrieve content of key ``val_map`` from ``item``.

        :param val_map: mapping of where to find certain data in `item` JSON
        :type val_map: :class:`unicode` OR :class:`list`
        :returns: all of ``item``'s values for the key
        :rtype: :class:`unicode`

        """
        if isinstance(val_map, unicode):  # highest JSON level
            result = item[val_map]
            if isinstance(result, unicode):
                result = [result]
        elif isinstance(val_map, list):   # JSON sub-level
            if isinstance(val_map[0], unicode) and len(val_map) == 2:
                [key, val] = val_map
                try:                    # key, val result is string
                    result = [item[key][val]]
                except TypeError:       # key, val result is list
                    result = [x[val] for x in item[key]]
                except KeyError:
                    result = []
            elif isinstance(val_map[0], list): # list of possible key, val pairs
                check = None
                for pair in val_map:
                    [key, val] = pair
                    try:
                        check = [item[key][val]]
                    except KeyError:
                        pass
                result = check if check != None else []
        else:
            result = []

        return ' '.join(result)

    @staticmethod
    def make_rank_func(weights):
        """Search ranking function.

        Use floats (1.0 not 1) for more accurate results. Use 0 to ignore a
        column.

        Adapted from <http://goo.gl/4QXj25> and <http://goo.gl/fWg25i>

        :param weights: list or tuple of the relative ranking per column.
        :type weights: :class:`tuple` OR :class:`list`
        :returns: a function to rank SQLITE FTS results
        :rtype: :class:`function`

        """
        def rank(matchinfo):
            """
            `matchinfo` is defined as returning 32-bit unsigned integers in
            machine byte order (see <http://www.sqlite.org/fts3.html#matchinfo>)
            and `struct` defaults to machine byte order.
            """
            bufsize = len(matchinfo)  # Length in bytes.
            matchinfo = [struct.unpack(b'I', matchinfo[i:i+4])[0]
                         for i in range(0, bufsize, 4)]
            it = iter(matchinfo[2:])
            return sum(x[0]*w/x[1]
                       for x, w in zip(zip(it, it, it), weights)
                       if x[1])
        return rank

    #-----------------------------------------------------------------------
    # SQLITE to JSON sub-methods
    #-----------------------------------------------------------------------

    def _execute(self, sql):
        """Execute sqlite query and return sqlite object.

        :param sql: SQL or SQLITE query string
        :type sql: :class:`unicode`
        :returns: SQLITE object of executed query
        :rtype: :class:`object`

        """
        cur = self.con.cursor()
        return cur.execute(sql)

    def _select(self, parts):
        """Prepare standard sqlite query string.

        :param parts: SQL or SQLITE query string
        :type parts: :class:`unicode`
        :returns: SQLITE object of executed query
        :rtype: :class:`object`

        """
        (sel, src, mtch, _id) = parts
        sql = """SELECT {sel} FROM {src} WHERE {mtch} = {id}"""
        query = sql.format(sel=sel, src=src, mtch=mtch, id=_id)
        return self._execute(query)
            
    #-----------------------------------------------------------------------
    # Individual Item Data
    #-----------------------------------------------------------------------

    def _item_type_name(self, item_type_id):
        """Get name of type from `item_type_id`

        :param item_type_id: ID number of item type in Zotero SQLITE
        :type item_type_id: :class:`int`
        :returns: name of specified type
        :rtype: :class:`unicode`

        """
        type_name = ''
        query_parts = ('typeName',
                      'itemTypes',
                      'itemTypeID',
                      item_type_id)
        (type_name,) = self._select(query_parts).fetchone()
        return type_name

    def _item_creators(self, item_id):
        """Generate array of dicts with item's creators' information.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: creator information for `item_id`
        :rtype: :class:`list`

        """
        result_array = []
        creators_query = ('creatorID, creatorTypeID, orderIndex',
                          'itemCreators',
                          'itemID', 
                          item_id)
        # iterate through all creators for this item
        for creator_info in self._select(creators_query):
            # save item's creator's ids to variables
            creator_id = creator_type_id = creator_id = order_index = ''
            (creator_id, 
             creator_type_id, 
             order_index) = creator_info
            # get key for this creator's information
            creators_id_query = ('creatorDataID',
                                 'creators',
                                 'creatorID',
                                 creator_id)
            (creator_data_id,) = self._select(creators_id_query).fetchone()
            # get this creator's information
            creator_info_sql = """
                SELECT creatorData.lastName, 
                    creatorData.firstName, creatorTypes.creatorType 
                FROM creatorData, creatorTypes
                WHERE
                    creatorDataID = {0}
                    and creatorTypeID = {1}""".format(creator_data_id, 
                                                      creator_type_id)
            creators_info = self._execute(creator_info_sql)
            # add all of this creator's info to the appropriate key
            for creator_info in creators_info:
                first_name = last_name = ''
                (last_name, 
                 first_name, 
                 c_type) = creator_info
                result_array.append({'family': last_name, 
                                              'given': first_name, 
                                              'type': c_type, 
                                              'index': order_index})
        return result_array

    def _item_metadata(self, item_id):
        """Generate array of dicts with all item's metadata.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: metadata information for `item_id`
        :rtype: :class:`dict`

        """
        item_meta = OrderedDict()
        # get all metadata for item
        metadata_id_query = ('fieldID, valueID',
                             'itemData',
                             'itemID',
                             item_id)
        items_data = self._select(metadata_id_query)
        # iterate thru metadata
        for _item in items_data:
            field_id = value_id = value_name = ''
            (field_id, 
             value_id) = _item
            # get metadata name
            field_name_query = ('fieldName',
                                'fields',
                                'fieldID',
                                field_id)
            (field_name,) = self._select(field_name_query).fetchone()
            # if unique metadata field
            if field_name not in item_meta:
                item_meta[field_name] = ''
                # get metadata value
                value_name_query = ('value',
                                    'itemDataValues',
                                    'valueID',
                                    value_id)
                (value_name,) = self._select(value_name_query).fetchone()
                if field_name == 'date':
                    item_meta[field_name] = value_name[0:4]
                else:
                    item_meta[field_name] = value_name
        return item_meta

    def _item_collections(self, item_id):
        """Generate an array or dicts with all of the `zotero` collections 
        in which the item resides.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: collection information for `item_id`
        :rtype: :class:`list`

        """
        all_collections = []
        # get all collection data for item
        coll_id_query = ('collectionID',
                         'collectionItems',
                         'itemID',
                         item_id)
        collections_data = self._select(coll_id_query)
        # iterate thru collections
        for _collection in collections_data:
            coll_id = ''
            (coll_id,) = _collection
            # get collection name for personal collections
            collection_info_sql = """
                SELECT collectionName, key
                FROM collections
                WHERE 
                    collectionID = {0}
                    and libraryID is null
            """.format(coll_id)
            collection_info = self._execute(collection_info_sql).fetchall()
            # if there are any personal collections
            if collection_info != []:
                (collection_name, 
                 collection_key) = collection_info[0]
                all_collections.append({'name': collection_name,
                                        'key': collection_key,
                                        'library_id': '0',
                                        'group': 'personal'})
            else:
                # get group collections
                #if self.personal_only == False:
                group_info_sql = """
                    SELECT collections.collectionName,
                        collections.key, groups.name, groups.libraryID
                    FROM collections, groups
                    WHERE 
                        collections.collectionID = {0}
                        and collections.libraryID is not null
                """.format(coll_id)
                (collection_name, 
                collection_key, 
                group_name, 
                library_id) = self._execute(group_info_sql).fetchone()
                all_collections.append({'name': collection_name,
                                        'key': collection_key,
                                        'library_id': library_id,
                                        'group': group_name})
        return all_collections

    def _item_tags(self, item_id):
        """Generate an array of dicts with all of the `zotero` tags
        assigned to the item.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: tag information for `item_id`
        :rtype: :class:`list`

        """
        all_tags = []
        # get all tag data for item
        tag_id_query = ('tagID',
                        'itemTags',
                        'itemID',
                        item_id)
        tags_data = self._select(tag_id_query)
        # iterate thru tags 
        for _tag in tags_data:
            tag_id = ''
            (tag_id,) = _tag
            # get tag name
            tag_info_query = ('name, key',
                              'tags',
                              'tagID',
                              tag_id)
            (tag_name,
             tag_key) = self._select(tag_info_query).fetchone()
            all_tags.append({'name': tag_name,
                             'key': tag_key})
        return all_tags

    def _item_attachments(self, item_id):
        """Generate an array or dicts with all of the item's attachments.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: attachment information for `item_id`
        :rtype: :class:`list`

        """
        all_attachments = []
        # get all attachment data for item
        attachment_info_query = ('path, itemID',
                                 'itemAttachments',
                                 'sourceItemID',
                                 item_id)
        attachments_data = self._select(attachment_info_query)
        # iterate thru attachments
        for _attachment in attachments_data:
            # if attachment has path
            if _attachment[0] != None:
                (att_path, 
                 attachment_id) = _attachment
                # if internal attachment
                if att_path[:8] == "storage:":
                    att_path = att_path[8:]
                    # if right kind of attachment
                    if True in (att_path.endswith(ext) for ext in ATTACH_EXTS):
                        # get attachment key
                        att_query = ('key',
                                     'items',
                                     'itemID',
                                     attachment_id)
                        (att_key,) = self._select(att_query).fetchone()
                        base = os.path.join(self.zotero.internal_storage,
                                                 att_key)
                        final_path = os.path.join(base,
                                                  att_path)
                        all_attachments.append({'name': att_path,
                                                        'key': att_key,
                                                        'path': final_path})
                # if external attachment
                elif att_path[:12] == "attachments:":
                    att_path = att_path[12:]
                    # if right kind of attachment
                    if True in (att_path.endswith(ext) for ext in ATTACH_EXTS):
                        # get attachment key
                        att_query = ('key',
                                     'items',
                                     'itemID',
                                     attachment_id)
                        (att_key,) = self._select(att_query).fetchone()
                        path = os.path.join(self.zotero.external_storage,
                                                  att_path)
                        all_attachments.append({'name': att_path,
                                                    'key': att_key,
                                                    'path': path})
                # if other kind of attachment
                else:
                    attachment_name = att_path.split('/')[-1]
                    all_attachments.append({'name': attachment_name,
                                            'key': None,
                                            'path': att_path})
        return all_attachments

    def _item_notes(self, item_id):
        """Generate an array of dicts with all of the item's notes.

        :param item_id: ID number of item in Zotero SQLITE
        :type item_id: :class:`int`
        :returns: note information for `item_id`
        :rtype: :class:`list`

        """
        all_notes = []
        # get all notes for item
        note_info_query = ('note',
                           'itemNotes',
                           'sourceItemID',
                           item_id)
        notes_data = self._select(note_info_query)
        # iterate thru notes
        for _note in notes_data:
            note = ''
            (note,) = _note
            # strip note HTML before adding
            all_notes.append(note[33:-10])
        return all_notes

#-------------------------------------------------------------------------------
# :class:`ZotAPI` ------------------------------------------------------------
#-------------------------------------------------------------------------------

class ZotAPI(object):
    """
    Zotero API (v.3) methods
    """
    def __init__(self, library_id=None, library_type=None, api_key=None):
        """ Store Zotero credentials
        """
        self.base = 'https://api.zotero.org'
        if library_id and library_type:
            self.library_id = library_id
            if library_type in ('user', 'group'):
                self.library_type = library_type + 's'
            else:
                raise RuntimeError('Invalid library type: %s' % library_type)
        if api_key:
            self.api_key = api_key
        self.request = None
        self.links = None

    def _retrieve_data(self, request=None, **kwargs):
        """
        Retrieve Zotero items via the API
        Combine endpoint and request to access the specific resource
        Returns an JSON object
        """
        full_url = '{}{}'.format(self.base, request)
        log.debug('API request: {}'.format(full_url))
        headers = {'User-Agent': "ZotQuery/{}".format(__version__),
                   'Authorization': "Bearer {}".format(self.api_key),
                   'Zotero-API-Version': 3}
        kwargs.update({'format': 'json'})
        self.request = web.get(url=full_url,
                               headers=headers,
                               params=kwargs)
        self.links = self._extract_links()
        self.request.raise_for_status()
        return self.request.json()

    def _prep_url(self, url, var=None):
        if var == None:
            return url.format(t=self.library_type,
                              u=self.library_id)
        else:
            return url.format(t=self.library_type,
                              u=self.library_id,
                              x=var)

    def _extract_links(self):
        try:
            links = self.request.headers['link']
            link_data = re.findall(r'<(.*?)>;\srel="(.*?)"', links)
            extracted = {}
            for link in link_data:
                url, key = link
                extracted[key] = url
            return extracted
        except KeyError:
            return None


    # No argument  -------------------------------------------------------------

    def items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items")
        return self._retrieve_data(url, **kwargs)

    def top_items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/top")
        return self._retrieve_data(url, **kwargs)

    def trash_items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/trash")
        return self._retrieve_data(url, **kwargs)

    def tags(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/tags")
        return self._retrieve_data(url, **kwargs)

    def collections(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections")
        return self._retrieve_data(url, **kwargs)

    def top_collections(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/top")
        return self._retrieve_data(url, **kwargs)

    # Requires Argument  -------------------------------------------------------

    def item(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``dict``
        """
        url = self._prep_url("/{t}/{u}/items/{x}", item_id)
        return self._retrieve_data(url, **kwargs)

    def collection(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``dict``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}", collection_id)
        return self._retrieve_data(url, **kwargs)

    ## -------------------------------------------------------------------------

    def item_children(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/{x}/children", item_id)
        return self._retrieve_data(url, **kwargs)

    def item_tags(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/{x}/tags", item_id)
        return self._retrieve_data(url, **kwargs)

    def tag(self, tag_name, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/tags/{x}", tag_name)
        return self._retrieve_data(url, **kwargs)

    def collection_children(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}/collections", collection_id)
        return self._retrieve_data(url, **kwargs)

    def collection_items(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}/items", collection_id)
        return self._retrieve_data(url, **kwargs)

    #TODO: broken
    def follow(self):
        """ Return the result of the call to the URL in the 'Next' link
        """
        if self.links:
            url = self.links.get('next')
            return self._retrieve_data(url)
        else:
            return None

    ## -------------------------------------------------------------------------

    ## Full Reference Read API requests  ---------------------------------------

    def item_reference(self, item, **kwargs):
        info = self.item(item,
                         include='bib',
                         **kwargs)
        return info['bib']

    def tag_references(self, tag_name, **kwargs):
        info = self.items(include='bib',
                          tag=tag_name,
                          itemtype='-attachment || note',
                          limit=100,
                          **kwargs)
        return [x['bib'] for x in info]

    def collection_references(self, collection, **kwargs):
        info = self.collection_items(collection,
                                     include='bib',
                                     itemtype='-attachment || note',
                                     limit=100,
                                     **kwargs)
        return [x['bib'] for x in info]

    ## -------------------------------------------------------------------------

    ## Short Citation Read API requests  ---------------------------------------

    def item_citation(self, item, **kwargs):
        info = self.item(item,
                         include='citation',
                         **kwargs)
        return info['citation']

#-------------------------------------------------------------------------------
# :class:`ZotWorkflow` 
#-------------------------------------------------------------------------------

class ZotWorkflow(object):
    """Represents all the Alfred Workflow actions.

    :param wf: a :class:`Workflow` instance.
    :type wf: :class:`object`

    """
    def __init__(self, wf):
        self.wf = wf
        self.flag = None
        self.arg = None
        self.zotquery = ZotQuery(self.wf)
        self.zotero = self.zotquery.zotero
        # set in `export` actions
        self.zot = None
        self.api = None
        self.prefs = None


  #-----------------------------------------------------------------------------
  ## Main API methods
  #-----------------------------------------------------------------------------

    def run(self, args):
        """Main API method.

        :param args: command line arguments passed to workflow
        :type args: :class:`dict`
        :returns: whatever the `method` returns
        :rtype: UNKOWN (see ind. methods for info)

        """
        self.flag = args['<flag>']
        self.arg = args['<argument>']
        # list of all possible actions
        actions = ('search', 'store', 'export', 'append',
                   'open', 'config', 'scan')
        for action in actions:
            if args.get(action):
                method_name = '{}_codepath'.format(action)
                method = getattr(self, method_name, None)
                if method:
                    return method()
                else:
                    raise ValueError('Unknown action: {}'.format(action))

    # `search` paths  ----------------------------------------------------------

    def search_codepath(self):
        """Search and show data for given scope and input query.

        """
        # Search for individual items
        if self.flag in SCOPE_TYPES['items']:
            self.search_items()
        # Search for individual groups
        elif self.flag in SCOPE_TYPES['groups']:
            self.search_groups()
        # Search for individual items in an individual group
        elif self.flag in SCOPE_TYPES['in-groups']:
            self.search_in_groups()
        # Search for certain debugging options
        elif self.flag in SCOPE_TYPES['meta']:
            self.search_debug()
        # Return whatever feedback is generated to Alfred
        self.wf.send_feedback()

    # `store` paths  -----------------------------------------------------------

    def store_codepath(self):
        """Store data in appropriate file.

        :returns: status of store process
        :rtype: :class:`boolean`

        """
        path = self.wf.cachefile('{}_query_result.txt'.format(self.flag))
        utils.path_write(self.arg, path)
        return True

    # `export` paths  ----------------------------------------------------------

    def export_codepath(self):
        """Use Zotero API to export formatted references.

        :returns: status of export process
        :rtype: :class:`boolean`

        """
        # Set `export` properties
        self.api = self.zotero.api_settings
        self.prefs = self.zotquery.output_settings
        self.zot = ZotAPI(library_id=self.api['user_id'],
                          library_type='user',
                          api_key=self.api['api_key'])
        # Retrieve HTML of item
        cites = self.get_export_html()
        # Export text of item to clipboard
        text = self.export_formatted(cites)
        utils.set_clipboard(text.strip())
        return self.prefs['fmt']

    def append_codepath(self):
        """Use Zotero API to export formatted references.

        :returns: status of export process
        :rtype: :class:`boolean`

        """
        # Set `export` properties
        self.api = self.zotero.api_settings
        self.prefs = self.zotquery.output_settings
        self.zot = ZotAPI(library_id=self.api['user_id'],
                          library_type='user',
                          api_key=self.api['api_key'])
        # Retrieve HTML of item
        cites = self.get_export_html()
        # Append text of temp biblio
        self.append_item(cites)
        return self.prefs['fmt']

    # `open` paths  ------------------------------------------------------------

    def open_codepath(self):
        """Open item or item's attachment.

        """
        self.prefs = self.zotquery.output_settings
        if self.flag == 'item':
            self.open_item()
        elif self.flag == 'attachment':
            self.open_attachment()

    # `config` paths  ----------------------------------------------------------

    def config_codepath(self):
        """Configure ZotQuery

        """
        if self.flag == 'freshen':
            self.config_freshen()
        elif self.flag == 'api':
            self.zotero.set_api()
        elif self.flag == 'prefs':
            self.zotquery.set_output()
        elif self.flag == 'all':
            self.zotero.set_api()
            self.zotquery.set_output()

    def scan_codepath(self):
        """Scan Markdown document for reference

        """
        self.prefs = self.zotquery.output_settings
        if self.flag == 'temp_bib':
            return self.read_temp_bib()
        else:
            md_text = utils.path_read(self.flag)
            self.reference_scan(md_text)

    def reference_scan(self, md_text):
        """Scan Markdown document for reference

        Adapted from <https://github.com/smathot/academicmarkdown>

        """
        ref_count = 0
        zot_items = []
        found_cks = []
        regexp = re.compile(r"(?:@|#)([^\s?!,.\t\n\r\v\]\[;#]+)")
        for reg_obj in re.finditer(regexp, md_text):
            cite_key = reg_obj.groups()[0]
            log.info("Found reference (#{}) {}".format(ref_count, cite_key))
            if cite_key in found_cks:
                continue
            ref_count += 1
            ck_parts = split_on_delimiters(cite_key)
            ck_query = ' '.join(ck_parts)
            matches = self._get_items(ck_query)
            if len(matches) == 0:
                log.debug('No matches for {}'.format(cite_key))
                return 1
            elif len(matches) > 1:
                log.debug('{} matches for {}'.format(len(matches), cite_key))
                log.debug("Matches: {}".format(matches))
                return 1
            match = matches[0]
            if match in zot_items and cite_key not in found_cks:
                for ck in sorted(found_cks):
                    log.debug('Ref: {}'.format(ck))
                raise Exception('"{}" refers to a pre-existent reference. \
                                Use consistent references (see log)!'.format(
                                                                      cite_key))
            zot_items.append(match)
            found_cks.append(cite_key)
        return zot_items


  #-----------------------------------------------------------------------------
  ### `Search` codepaths
  #-----------------------------------------------------------------------------

    # Search debugging meta options  -------------------------------------------

    def search_debug(self):
        """Debug options Filter method.

        """
        self.wf.add_item("Root", "Open ZotQuery's Root Folder?", 
            valid=True, 
            arg='workflow:openworkflow', 
            icon='icons/n_folder.png')
        self.wf.add_item("Storage", "Open ZotQuery's Storage Folder?", 
            valid=True, 
            arg='workflow:opendata', 
            icon='icons/n_folder.png')
        self.wf.add_item("Cache", "Open ZotQuery's Cache Folder?", 
            valid=True, 
            arg='workflow:opencache', 
            icon='icons/n_folder.png')
        self.wf.add_item("Logs", "Open ZotQuery's Logs?", 
            valid=True, 
            arg='workflow:openlog', 
            icon='icons/n_folder.png')

    # --------------------------------------------------------------------------

    # Search individual `items`  -----------------------------------------------

    def search_items(self):
        """Search individual items.

        """
        # Get JSON data of user's Zotero library
        data = utils.json_read(self.zotquery.json_data)
        # Get keys of all items that match specific query
        keys = self._get_items()
        for key in keys:
            # Ignore rank score
            key = key[-1]
            # Get JSON info for that item
            item = data.get(key, None)
            if item:
                # Prepare dictionary for Alfred
                alfred = self._prepare_item_feedback(item)
                self.wf.add_item(**alfred)

    # Search Zotero `groups`  --------------------------------------------------

    def search_groups(self):
        """Search thru Zotero groups.

        """
        # Get keys of all groups that match specific query
        groups = self._get_groups()
        for group in groups:
            # Prepare dictionary for Alfred
            alfred = self._prepare_group_feedback(group)
            self.wf.add_item(**alfred)

    # Search within Zotero `groups`  -------------------------------------------

    def search_in_groups(self):
        """Search for items within selected group.

        """
        # Get name of group stored in cache
        group = self._get_group_name()
        # Get keys of all items that match query in `group`
        keys = self._get_in_group(group)
        # Get JSON data of user's Zotero library
        data = utils.json_read(self.zotquery.json_data)
        for key in keys:
            # Ignore rank score
            key = key[-1]
            # Get JSON info for that item
            item = data.get(key, None)
            if item:
                # Prepare dictionary for Alfred
                alfred = self._prepare_item_feedback(item)
                self.wf.add_item(**alfred)

    ## -------------------------------------------------------------------------

    ## Get keys of individual `items`  -----------------------------------------

    def _get_items(self, arg=None):
        """Search the FTS database for query.

        :returns: all items that match query
        :rtype: :class:`list`

        """
        query = self.arg if arg == None else arg
        # Prepare proper `sqlite` query for individual items
        sql = self._make_items_query(query)
        log.info('Item sqlite query: {}'.format(sql.strip()))
        # Search against either Unicode or ASCII database
        if not isascii(query):
            db = self.zotquery.fts_sqlite
        else:
            db = self.zotquery.folded_sqlite
        log.info('Connecting to: {}'.format(db))
        con = sqlite3.connect(db)
        # Prepare ranking weights (all columns equal weight)
        ranks = [1.0] * len(FILTERS['general'])
        with con:
            # Generate ranking function
            con.create_function('rank', 1, self.zotquery.make_rank_func(ranks))
            # Query FTS database and get result keys
            results = self._do_sqlite(con, sql)
        return results

    ## Get name and key of Zotero `groups`  ------------------------------------

    def _get_groups(self):
        """Get name and key for all groups that match query.

        :returns: all items that match query
        :rtype: :class:`list`

        """
        # Prepare proper `sqlite` query for Zotero groups
        sql = self._make_group_query()
        log.info('Group sqlite query: {}'.format(sql.strip()))
        db = self.zotquery.cloned_sqlite
        con = sqlite3.connect(db)
        with con:
            # Query cloned database and get result keys
            results = self._do_sqlite(con, sql)
        return results

    ## Get name of `group` in cache  -------------------------------------------

    def _get_group_name(self):
        """Get name of group from stored result.

        :returns: name of group from it's ID
        :rtype: :class:`unicode`

        """
        # get group type (`collection` vs `tag`)
        flag = self.flag.split('-')[1]
        # Read saved group info
        path = self.wf.cachefile('{}_query_result.txt'.format(flag))
        group_id = utils.path_read(path)
        # Split group type from group ID
        kind, uid = group_id.split('_')
        if kind == 'c':
            group = self._get_collection_name(uid)
        elif kind == 't':
            group = self._get_tag_name(uid)
        return group

    ## Get keys of `items` in Zotero `group`  ---------------------------------

    def _get_in_group(self, group):
        """Get keys for all items that match query.

        :param group: name of stored group
        :type group: :class:`unicode`
        :returns: item keys
        :rtype: :class:`list`

        """
        # Prepare proper `sqlite` query for searching in Zotero groups
        sql = self._make_in_group_query(group)
        log.info('In-Group sqlite query: {}'.format(sql.strip()))
        # Search against either Unicode or ASCII database
        if not isascii(self.arg):
            db = self.zotquery.fts_sqlite
        else:
            db = self.zotquery.folded_sqlite
        log.info('Connecting to: {}'.format(db))
        con = sqlite3.connect(db)
        with con:
            # Query FTS database and get result keys
            results = self._do_sqlite(con, sql)
        return results

    ### ------------------------------------------------------------------------

    ### Query maker for searching Zotero `items`  ------------------------------

    def _make_items_query(self, arg=None):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get all items' keys.

        :returns: SQLITE query string for ind. items
        :rtype: :class:`unicode`

        """
        sql = """SELECT key
            FROM zotquery
            WHERE zotquery MATCH '{}'
        """
        # Make query term fuzzy searched
        if arg == None:
            fuzzy_term = '*' + self.arg + '*'
        else:
            fuzzy_term = '*' + arg + '*'
        # if `general`, search all columns
        final = fuzzy_term
        if self.flag == 'general':
            final = fuzzy_term
        # if scoped, search only relevant columns
        elif self.flag in FILTERS.keys():
            # Which columns for scope?
            columns = FILTERS.get(self.flag)
            columns.remove('key')
            # Format `column:query`
            bits = ['{}:{}'.format(col, fuzzy_term) for col in columns]
            # Make a disjunctive query
            final = ' OR '.join(bits)
        return sql.format(final)

    ### Query maker for searching Zotero `groups`  -----------------------------

    def _make_group_query(self):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get group name and key.

        :returns: SQLITE query string for ind. groups
        :rtype: :class:`unicode`

        """
        sql = """SELECT {col}, key
                FROM {table}
                WHERE {col} LIKE '{query}'
        """
        # Make query term fuzzy searched
        fuzzy_term = '%' + self.arg + '%'
        # What column name to get `name`?
        if self.flag == 'collections':
            col = 'collectionName'
        elif self.flag == 'tags':
            col = 'name'
        return sql.format(col=col,
                          table=self.flag,
                          query=fuzzy_term)

    ### Query maker for searching in Zotero `groups`  --------------------------

    def _make_in_group_query(self, group):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get items' keys for specified ``group``.

        :param group: name of collection or tag to search within
        :type group: :class:`unicode`
        :returns: SQLITE query string for ind. items in group
        :rtype: :class:`unicode`

        """
        sql = """SELECT key
                FROM zotquery
                WHERE zotquery MATCH '{}'
        """
        # Make query term fuzzy searched
        fuzzy_term = '*' + self.arg + '*'
        # Prepare column name from ``flag``
        flag = self.flag.split('-')[1] + 's'
        # Prepare in-column search
        specifier = ':'.join([flag, group])
        # Make conjunctive query
        query = ' AND '.join([fuzzy_term, specifier])
        return sql.format(query)

    ### Perform `sqlite` query (w/ error handling)  ----------------------------

    def _do_sqlite(self, con, sql):
        """Perform sqlite query.

        :param con: SQLITE connection object
        :type con: :class:`object`
        :param con: SQLITE query string
        :type con: :class:`unicode`

        """
        with con:
            cur = con.cursor()
            try:
                cur.execute(sql)
                results = cur.fetchall()
            except sqlite3.OperationalError as err:
                # If the query is invalid, show an appropriate warning and exit
                if b'malformed MATCH' in err.message:
                    self.wf.add_item('Invalid query', icon=ICON_WARNING)
                    self.wf.send_feedback()
                    return 1
                # Otherwise raise error for Workflow to catch and log
                else:
                    raise err
        return results

    #### -----------------------------------------------------------------------

    #### Get name of `collection` from `key`  ----------------------------------

    def _get_collection_name(self, key):
        """Get name of tag from `key`"""
        db = self.zotquery.cloned_sqlite
        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            sql_query = """SELECT collectionName
                FROM collections
                WHERE key = "{}" """.format(key)
            col_name = cur.execute(sql_query).fetchone()
        return col_name[0]

    #### Get name of `tag` from `key`  -----------------------------------------

    def _get_tag_name(self, key):
        """Get name of tag from `key`"""
        db = self.zotquery.cloned_sqlite
        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            sql_query = """SELECT name
                FROM tags
                WHERE key = "{}" """.format(key)
            tag_name = cur.execute(sql_query).fetchone()
        return tag_name[0]

    #### Prepare Alfred dictionary of `item` for feedback  ---------------------

    def _prepare_item_feedback(self, item):
        """Format the subtitle string for ``item``

        """
        icn_type = 'n'
        alfred = {}
        alfred['title'] = self._format_title(item)
        # Format item's subtitle
        subtitle = ' '.join([self._format_creator(item),
                             self._format_date(item)])
        if item['attachments'] != []:
            icn_type = 'att'
            subtitle = ' '.join([subtitle, 'Attachments:',
                                str(len(item['attachments']))])
        alfred['subtitle'] = subtitle
        alfred['valid'] = True
        alfred['arg'] = '_'.join([str(item['library']), str(item['key'])])
        alfred['icon'] = self._format_icon(item, icn_type)
        if LARGE_TEXT:
            alfred['largetext'] = self._format_largetext(item)
        if QUICK_COPY:
            alfred['copytext'] = self._format_quickcopy(item)
        if ALFRED_LEARN:
            alfred['uid'] = str(item['id'])
        return alfred

    #### Prepare Alfred dictionary of `group` for feedback  --------------------

    def _prepare_group_feedback(self, group):
        """Prepare Alfred data for groups.

        """
        name, key = group
        alfred = {}
        alfred['title'] = name
        alfred['subtitle'] = self.flag[:-1].capitalize()
        alfred['valid'] = True
        alfred['arg'] = '_'.join([self.flag[0], key])
        alfred['icon'] = "icons/n_{}.png".format(self.flag[:-1])
        if ALFRED_LEARN:
            alfred['uid'] = str(key)
        return alfred

    ##### ----------------------------------------------------------------------

    ##### Properly format `item`'s title  --------------------------------------

    @staticmethod
    def _format_title(item):
        """Properly format the title information for ``item``.

        """
        try:
            if not item['data']['title'][-1] in ('.', '?', '!'):
                title_final = item['data']['title'] + '.'
            else:
                title_final = item['data']['title']
        except KeyError:
            title_final = 'xxx.'
        return title_final

    ##### Properly format `item`'s creator info  -------------------------------

    @staticmethod
    def _format_creator(item):
        """Properly format the creator information for ``item``.

        """
        creator_list = []
        # Order last names by index
        for author in item['creators']:
            last = author['family']
            index = author['index']
            if author['type'] == 'editor':
                last = last + ' (ed.)'
            elif author['type'] == 'translator':
                last = last + ' (trans.)'
            creator_list.insert(index, last)
        # Format last names into string
        if len(item['creators']) == 0:
            creator_ref = 'xxx.'
        elif len(item['creators']) == 1:
            creator_ref = ''.join(creator_list)
        elif len(item['creators']) == 2:
            creator_ref = ' and '.join(creator_list)
        elif len(item['creators']) > 2:
            creator_ref = ', '.join(creator_list[:-1])
            creator_ref = creator_ref + ', and ' + creator_list[-1]
        # Format final period (`.`)
        if not creator_ref[-1] in ('.', '!', '?'):
            creator_ref = creator_ref + '.'
        return creator_ref

    ##### Properly format `item`'s date  ---------------------------------------

    @staticmethod
    def _format_date(item):
        """Properly format the date information for ``item``.

        """
        try:
            return str(item['data']['date']) + '.'
        except KeyError:
            return 'xxx.'

    ##### Properly format `item`'s icon  ---------------------------------------

    @staticmethod
    def _format_icon(item, icn_type):
        """Properly format the icon for ``item``.

        """
        icon = 'icons/{}_written.png'.format(icn_type)
        if item['type'] == 'journalArticle':
            icon = 'icons/{}_article.png'.format(icn_type)
        elif item['type'] == 'book':
            icon = 'icons/{}_book.png'.format(icn_type)
        elif item['type'] == 'bookSection':
            icon = 'icons/{}_chapter.png'.format(icn_type)
        elif item['type'] == 'conferencePaper':
            icon = 'icons/{}_conference.png'.format(icn_type)
        return icon

    ##### Properly format `item`'s largetext  ----------------------------------

    def _format_largetext(self, item):
        """Generate `str` to be displayed by Alfred's large text.

        """
        if isinstance(LARGE_TEXT, unicode):
            # get search map from column
            json_map = FILTERS_MAP.get(LARGE_TEXT, None)
            if json_map:
                # get data from `item` using search map
                largetext = self.zotquery.get_datum(item, json_map)
        elif hasattr(LARGE_TEXT, '__call__'):
            largetext = LARGE_TEXT(item)
        else:
            largetext = ''
        return largetext

    ##### Properly format `item`'s quickcopy text  -----------------------------

    def _format_quickcopy(self, item):
        """Generate `str` to be copied to clipboard by `cmd+c`.

        """
        if isinstance(QUICK_COPY, unicode):
            # get search map from column
            json_map = FILTERS_MAP.get(QUICK_COPY, None)
            if json_map:
                # get data from `item` using search map
                quickcopy = self.zotquery.get_datum(item, json_map)
        elif hasattr(QUICK_COPY, '__call__'):
            quickcopy = QUICK_COPY(item)
        else:
            quickcopy = ''
        return quickcopy


  #-----------------------------------------------------------------------------
  ### `Export` method
  #-----------------------------------------------------------------------------
    
    # Retrieve HTML of item  ---------------------------------------------------

    def get_export_html(self):
        """Get HTML of item reference.

        """
        # check if item reference has already been generated and cached
        no_cache = True
        cached = self.wf.cached_data(self.arg, max_age=0)
        if cached:
            # check if item reference is right kind
            if self.flag in cached.keys():
                cites = cached[self.flag]
                no_cache = False
        # if not exported before
        if no_cache:
            # Choose appropriate code branch
            if self.flag in ('bib', 'citation'):
                cites = self.export_item()
            elif self.flag == 'group':
                cites = self.export_group()
            # Cache exported HTML?
            if CACHE_REFERENCES:
                cache = {self.flag: cites}
                self.wf.cache_data(self.arg, cache)
        return cites

    ## -------------------------------------------------------------------------

    ## Export individual `items`  ----------------------------------------------

    def export_item(self):
        """Export individual item in preferred format.

        """
        item_id = self.arg.split('_')[1]
        cite = self.zot.item(item_id,
                             include=self.flag,
                             style=self.prefs['csl'])
        return cite[self.flag]

    ## Export entire `tag` or `collection`  ------------------------------------

    def export_group(self):
        """Export entire group in preferred format.

        """
        group_type, item_id = self.arg.split('_')
        if group_type == 'c':
            cites = self.zot.collection_references(item_id,
                                                   style=self.prefs['csl'])
        elif group_type == 't':
            tag_name = self._get_tag_name(item_id)
            cites = self.zot.tag_references(tag_name,
                                            style=self.prefs['csl'])
        return '\n'.join(cites)

    ### ------------------------------------------------------------------------

    ### Append `item` to temporary bibliography  -------------------------------

    def append_item(self, cites):
        """Append citation to appropriate bibliography file.

        """
        path = "temp_bibliography.html"
        text = self._prepare_html(cites)
        path = self.wf.cachefile(path)
        with open(path, 'a') as file_obj:
            file_obj.write(text.strip().encode('utf-8'))


    def read_temp_bib(self):
        """Read content of temporary bibliography.

        """
        path = self.wf.cachefile("temp_bibliography.html")
        bib = utils.path_read(path)
        text = self.export_formatted(bib)
        utils.set_clipboard(text)
        return self.prefs['fmt']


    ### Export properly formatted text  ----------------------------------------

    def export_formatted(self, cites):
        """Format the HTML citations in the proper format.

        """
        if self.prefs['fmt'] == 'Markdown':
            final = self._export_markdown(cites)
        elif self.prefs['fmt'] == 'Rich Text':
            final = self._export_rtf(cites)
        return final

    #### -----------------------------------------------------------------------

    #### Export text as Markdown  ----------------------------------------------

    def _export_markdown(self, html):
        """Convert to Markdown

        """
        html = self._preprocess(html)
        markdown = html2text.html2text(html, bodywidth=0)
        if self.flag == 'bib':
            markdown = re.sub(r"_(.*?)_", r"*\1*", markdown, re.S)
        elif self.flag == 'citation':
            if self.prefs['csl'] == 'bibtex':
                markdown = '[@' + markdown.strip() + ']'
        return markdown

    #### Export text as Rich Text  ---------------------------------------------

    def _export_rtf(self, html):
        """Convert to RTF

        """
        path = self.wf.cachefile("temp_export.html")
        html = self._prepare_html(html)
        if self.flag == 'citation':
            if self.prefs['csl'] == 'bibtex':
                html = '[@' + html.strip() + ']'
        utils.path_write(html, path)
        rtf = self.html2rtf(path)
        return rtf

    ##### ----------------------------------------------------------------------

    ##### Clean up and stringify HTML  -----------------------------------------

    def _prepare_html(self, html):
        """Prepare HTML

        """
        html = self._preprocess(html)
        return html.encode('ascii', 'xmlcharrefreplace')

    ##### Convert HTML to Rich Text  -------------------------------------------

    @staticmethod
    def html2rtf(path):
        """Convert html to RTF and copy to clipboard"""
        return subprocess.check_output(['textutil',
                                        '-convert',
                                        'rtf',
                                        path,
                                        '-stdout'])

    ##### Clean up odd formatting  ---------------------------------------------

    def _preprocess(self, item):
        """Clean up `item` formatting"""
        if self.prefs['csl'] != 'bibtex':
            item = re.sub(r"(http|doi)(.*?)\.(?=<)(.*?)\.(?=<)", "", item)
        item = re.sub("’", "'", item)    
        item = re.sub("pp. ", "", item)
        return item


  #-----------------------------------------------------------------------------
  ### `Open` method
  #-----------------------------------------------------------------------------

    # Open individual `items`  -------------------------------------------------

    def open_item(self):
        """Open item in Zotero client"""
        if self.prefs['app'] == "Standalone":
            app_id = "org.zotero.zotero"
        elif self.prefs['app'] == "Firefox":
            app_id = "org.mozilla.firefox"

        scpt_str = """
            if application id "{1}" is not running then
                tell application id "{1}"
                    activate
                    delay 0.5
                    activate
                    delay 0.5
                    open location "zotero://select/items/" & "{0}"
                end tell
            else
                tell application id "{1}"
                    activate
                    delay 0.5
                    open location "zotero://select/items/" & "{0}"
                end tell
            end if
            """.format(self.arg, app_id)
        return utils.run_applescript(scpt_str)

    # Open `item`'s attachment  ------------------------------------------------

    def open_attachment(self):
        """Open item's attachment in default app"""
        if os.path.isfile(self.arg):
            subprocess.Popen(['open', self.arg], stdout=subprocess.PIPE)
        # if self.input is item key
        else:
            data = utils.json_read(self.zotquery.json_data)
            item_id = self.arg.split('_')[1]
            item = data.get(item_id, None)
            if item:
                for att in item['attachments']:
                    if os.path.exists(att['path']):
                        subprocess.check_output(['open', att['path']])


  #-----------------------------------------------------------------------------
  ### `Config` codepaths
  #-----------------------------------------------------------------------------

    def config_freshen(self):
        """Update relevant data stores.

        """
        if self.arg == 'True':
            self.zotquery.update_clone()
            self.zotquery.update_json()
            return 0
        update, spot = self.zotquery.is_fresh()
        if update == True:
            if spot == 'Clone':
                self.zotquery.update_clone()
            elif spot == 'JSON':
                self.zotquery.update_json()
        return 0

#-------------------------------------------------------------------------------
# Main Script
#-------------------------------------------------------------------------------

def main(wf):
    """Accept Alfred's args and pipe to proper Class"""

    args = wf.args
    #args = ['search', 'debug']
    args = docopt(__usage__, argv=args, version=__version__)
    log.info(args)
    pd = ZotWorkflow(wf)
    res = pd.run(args)
    if res:
        print(res)


if __name__ == '__main__':
    WF = Workflow()
    # create global methods from `Workflow()`
    log = WF.logger
    decode = WF.decode
    fold = WF.fold_to_ascii
    sys.exit(WF.run(main))
