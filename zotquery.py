#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 06-08-2014
#
from __future__ import unicode_literals

# Standard Library
import os
import re
import sys
import json
import struct
import sqlite3
import os.path
import subprocess
from time import time
from shutil import copyfile
from collections import OrderedDict

# Internal Dependencies
import utils
import pashua
from workflow import Workflow, bundler

#from workflow.workflow import MATCH_ALL, MATCH_ALLCHARS
# Use bundler for External Dependencies
#import bundler
#bundler.init()
#import html2text
#from pyzotero import zotero


__version__ = '0.1'
# TODO: add logging

__usage__ = """
ZotQuery -- An Alfred GUI for `zotero`

Usage:
    zotquery.py cache <force> <personal_only>
    zotquery.py config <method>
    zotquery.py filter <query> <scope>
    zotquery.py action <key> <command>

Arguments:
    <force>         Boolean; update cache regardless of freshness?
    <personal_only> Boolean; restrict cached data to user's personal library?
    <method>        String; api, prefs, or paths
    <query>         String; term(s) for searching ZotQuery db
    <scope>         String; general, titles, creators, collections, tags, notes, 
                            attachments, in-collection, in-tag, debug, new
    <key>           String; item's Zotero key
    <command>       String; cite, ref, cite_group, append, save_coll, 
                            save_tag, att, bib, open
"""

# Path to apps
STANDALONE = os.path.expanduser('~/Library/Application Support/Zotero/')
FIREFOX = os.path.expanduser('~/Library/Application Support/Firefox/')

ATTACHMENT_EXTS = [".pdf", "epub"]      # Needs to be 4 chars long

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

FILTERS = {
    'general': [
        'key', 'title', 'creators', 'collection_title',
        'date', 'tags', 'collections'
    ], 
    'titles': [
        'key', 'title', 'collection_title', 'date'
    ], 
    'creators': [
        'key', 'creators', 'date'
    ],
    'tag': [
        'key', 'tags'
    ], 
    'collection': [
        'key', 'collections'
    ], 
    'attachments': [
        'key', 'attachments'
    ], 
    'notes': [
        'key', 'notes'
    ]
}

PASHUA = bundler.utility('pashua')

# Will be populated later
log = None
decode = None

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
        self.zotero = self.paths

    # `self.zotero` setter property --------------------------------------------

    @property
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
        zotero = self.wf.stored_data('zotero_paths')
        if zotero == None: #if paths cache doesn't exist
            paths = {
                'original_sqlite': self._original_sqlite,
                'internal_storage': self._internal_storage,
                'external_storage': self._external_storage
            }
            self.wf.store_data('zotero_paths', paths,
                                serializer='json')
            zotero = paths
        return zotero

    def set_api(self):
        """Configure Zotero API data.
        """
        conf = """
        # Set window title
        *.title = Zotero API Settings

        #Add a text field
        api.type = textfield
        api.label = Enter your Zotero API Key
        api.width = 310

        id.type = textfield
        id.label = Enter your Zotero User ID
        id.width = 310

        # Add a cancel button with default label
        cb.type=cancelbutton
        """
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=PASHUA)
        if res_dict['cb'] != 1:
            self.wf.save_password('zotero_api', res_dict['api'])
            self.wf.save_password('zotero_user', res_dict['id'])

    @property
    def api_settings(self):
        """Retrieve user's Keychain stored Zotero API settings.
        """
        api_key = self.wf.get_password('zotero_api')
        user_id = self.wf.get_password('zotero_user')
        user_type = 'user'
        return {
            'api_key': api_key,
            'user_id': user_id,
            'user_type': user_type
        }

    # `self.zotero` sub-properties ---------------------------------------------

    @property
    def _original_sqlite(self):
        """Return path to Zotero's internal sqlite database.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.zotero['original_sqlite']
        except AttributeError:
            sqlites = self.find_name('zotero.sqlite')
            return None if sqlites == [] else sqlites[0]

    @property
    def _internal_storage(self):
        """Return path to Zotero's internal storage directory for attachments.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to directory
        :rtype: :class:`unicode`

        """
        try:
            return self.zotero['internal_storage']
        except AttributeError:
            zotero_dir = os.path.dirname(self._original_sqlite)
            storage_dir = os.path.join(zotero_dir, 'storage')
            if os.path.exists(storage_dir):
                return storage_dir
            else:
                for name in ('dataDir', 'lastDataDir'):
                    dir_pref = self.get_pref(name)
                    if dir_pref != None:
                        return dir_pref

    @property
    def _external_storage(self):
        """Return path to Zotero's external storage directory for attachments.

        Expects information in :file:`zotero_paths.json`.
        If file doesn't exist, it finds path manually.

        :returns: full path to directory
        :rtype: :class:`unicode`

        """
        try:
            return self.zotero['external_storage']
        except AttributeError:
            return self.get_pref('baseAttachmentPath')

    # `self.zotero` utility methods --------------------------------------------

    def get_pref(self, pref):
        """Retrieve the value for ``pref`` in Zotero's preferences.

        :param pref: name of desired Zotero preference
        :type pref: :class:`unicode` or :class:`str`

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
        self.zotero = Zotero(self.wf).zotero
        self.zotquery = self.paths
        self.con = None

    # `self.zotquery` setter property ------------------------------------------

    @property
    def paths(self):
        """Dictionary of paths to relevant ZotQuery data:
            ==================      ============================================
            Key                     Description
            ==================      ============================================
            `cloned_sqlite`         ZotQuery's clone of Zotero's sqlite database
            `json_data`             ZotQuery's JSON clone of Zotero's sqlite
            `fts_sqlite`            ZotQuery's Full Text Search database

        Expects information to be stored in data file ``zotquery_paths.json``.
        If file does not exist, :prop:`paths` creates and stores dictionary.

        :returns: key ZotQuery paths
        :rtype: :class:`dict`

        """
        zotquery = self.wf.stored_data('zotquery_paths')
        if zotquery == None: #if paths cache doesn't exist
            paths = {
                'cloned_sqlite': self._cloned_sqlite,
                'json_data': self._json_data,
                'fts_sqlite': self._fts_sqlite
            }
            self.wf.store_data('zotquery_paths', paths,
                                serializer='json')
            zotquery = paths
        return zotquery

    def set_output(self):
        """Configure Zotero API data.
        """
        conf = """
        # Set window title
        *.title = ZotQuery Output Preferences

        # Define Zotero app
        app.type = radiobutton
        app.label = Select your Zotero application client:
        app.option = Standalone
        app.option = Firefox
        app.default = Standalone

        # Define CSL style
        csl.type = radiobutton
        csl.label = Select your your desired CSL style:
        csl.option = chicago-author-date
        csl.option = apa
        csl.option = modern-language-association
        csl.option = rtf-scan
        csl.option = bibtex
        csl.option = odt-scannable-cites
        csl.default = chicago-author-date

        # Define output format
        fmt.type = radiobutton
        fmt.label = Select your desired output format:
        fmt.option = Markdown
        fmt.option = Rich Text
        fmt.default = Markdown

        # Add a cancel button with default label
        cb.type=cancelbutton
        """
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=PASHUA)
        if res_dict['cb'] != 1:
            del res_dict['cb']
            self.wf.store_data('output_settings', res_dict, serializer='json')

    @property
    def output_settings(self):
        """Retrieve user chosen output settings.
        """
        return self.wf.stored_data('output_settings')

    # `self.zotquery` sub-properties -------------------------------------------

    @property
    def _cloned_sqlite(self):
        """Return path to ZotQuery's cloned sqlite database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it creates the file by cloning
        ``original_sqlite`` from :attr:`Zotero.paths`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.zotquery['cloned_sqlite']
        except AttributeError:
            clone_path = self.wf.datafile("zotquery.sqlite")
            if not os.path.exists(clone_path):
                copyfile(self.zotero['original_sqlite'], clone_path)
            return clone_path

    @property
    def _json_data(self):
        """Return path to ZotQuery's JSON version of user's Zotero database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it generates the file with data
        from :attr:`ZotQuery._cloned_sqlite`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            json_path = self.zotquery['json_data']
        except AttributeError:
            json_path = self.wf.datafile("zotquery.json")
            if not os.path.exists(json_path):
                self.con = sqlite3.connect(self._cloned_sqlite)
                self.to_json()
        return json_path

    @property
    def _fts_sqlite(self):
        """Return path to ZotQuery's Full Text Search sqlite database.

        Expects information in :file:`zotquery_paths.json`.
        If file doesn't exist, it creates the database then
        fills it with data from :attr:`ZotQuery._json_data`.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        try:
            return self.zotquery['fts_sqlite']
        except AttributeError:
            fts_path = self.wf.datafile("zotquery.db")
            if not os.path.exists(fts_path):
                self.create_index_db(fts_path)
                self.update_index_db(fts_path)
            return fts_path

    # `self.zotquery` utility methods ------------------------------------------

    def is_fresh(self):
        """Is ZotQuery up-to-date with Zotero?

        Two specific questions:
            + is ``_cloned_sqlite`` parallel to :attr:`Zotero._original_sqlite`?
            + is ``_json_data`` parallel to ``_cloned_sqlite``?

        :returns: tuple with Boolean answer and rotten file
        :rtype: :class:`tuple`

        """
        (update, spot) = (False, None)
        zotero_mod = os.stat(self.zotero['original_sqlite'])[8]
        clone_mod = os.stat(self._cloned_sqlite)[8]
        cache_mod = os.stat(self._json_data)[8]
        # Check if cloned sqlite database is up-to-date with `zotero` database
        if zotero_mod > clone_mod:
            update, spot = (True, "Clone")
        # Check if JSON cache is up-to-date with the cloned database
        elif (cache_mod - clone_mod) > 10:
            update, spot = (True, "JSON")
        return update, spot

    @staticmethod
    def create_index_db(db):
        """Create FTS virtual table with data from ``_json_data``"""

        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            # TODO: add user customization option
            columns = FILTERS.get('general', None)
            if columns:
                columns = ', '.join(columns)
                sql = """CREATE VIRTUAL TABLE zotquery
                         USING fts3({columns})""".format(columns=columns)
                cur.execute(sql)

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
        all_items = {}
        info_sql = """
            SELECT key, itemID, itemTypeID, libraryID
            FROM items
            WHERE 
                itemTypeID not IN (1, 13, 14)
            ORDER BY dateAdded DESC
        """
        basic_info = self._execute(info_sql)

        for basic in basic_info:
            # prepare item's root dict and metadata dict
            item_dict = OrderedDict()

            # save item's basic ids to variables
            item_key = item_id = item_type_id = library_id = ''
            (item_key,
             item_id,
             item_type_id,
             library_id) = basic
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

            all_items[item_key] = item_dict

        self._close()
        self.wf.store_data('zotquery', all_items, serializer='json')


    # JSON to FTS sub-methods --------------------------------------------------

    def update_index_db(self, fts_path):
        """Update ``_fts_sqlite`` with JSON data from ``_json_data``.

        Reads in data from ``_json_data`` and adds it to the FTS database.

        """

        start = time()
        con = sqlite3.connect(fts_path)
        count = 0
        with con:
            cur = con.cursor()
            for row in self.generate_data():
                columns = ', '.join([x.keys()[0] for x in row])
                values = ['"' + x.values()[0].replace('"', "'") + '"'
                            for x in row]
                values = ', '.join(values)
                sql = """INSERT OR IGNORE INTO zotquery
                         ({columns}) VALUES ({data})
                        """.format(columns=columns, data=values)
                cur.execute(sql)
                count += 1
                
        print '{} items added/updated in {:0.3} seconds'.format(
                 count, time() - start)

    def generate_data(self):
        """Create a genererator with dictionaries for each item
        in ``_json_data``.

        :returns: ``list`` of ``dicts`` with all item's data as ``strings``
        :rtype: :class:`genererator`
        """
        json_data = utils.json_read(self._json_data)
        for item in json_data.itervalues():
            array = list()
            columns = FILTERS.get('general', None)
            if columns:
                for column in columns:
                    json_map = FILTERS_MAP.get(column, None)
                    if json_map:
                        array.append({column: self.get_datum(item, json_map)})
            yield array

    @staticmethod
    def get_datum(item, val_map):
        """Retrieve content of key ``val_map`` from ``item``.

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
        `weights` is a list or tuple of the relative ranking per column.

        Use floats (1.0 not 1) for more accurate results. Use 0 to ignore a
        column.

        Adapted from <http://goo.gl/4QXj25> and <http://goo.gl/fWg25i>
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
        """
        
        cur = self.con.cursor()
        return cur.execute(sql)

    def _close(self):
        """Close connection to sqlite database.
        """
        self.con.close()

    def _select(self, parts):
        """Prepare sqlite query string.
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
                    if att_path[-4:].lower() in ATTACHMENT_EXTS:
                        # get attachment key
                        att_query = ('key',
                                     'items',
                                     'itemID',
                                     attachment_id)
                        (att_key,) = self._select(att_query).fetchone()
                        base = os.path.join(self.zotero['internal_storage'],
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
                    if att_path[-4:].lower() in ATTACHMENT_EXTS:
                        # get attachment key
                        att_query = ('key',
                                     'items',
                                     'itemID',
                                     attachment_id)
                        (att_key,) = self._select(att_query).fetchone()
                        path = os.path.join(self.zotero['external_storage'],
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


class ZotWorkflow(object):
    def __init__(self, wf):
        self.wf = wf

    def do_config(self):
        """Configure ZotQuery

        Takes many steps:
            + Find and save all key Zotero paths
            + Find and save all key ZotQuery paths
            + Clone Zotero sqlite to ``zotquery.sqlite``
            + Convert ``zotquery.sqlite`` to ``zotquery.json``
            + Generate ``zotquery.db`` for full text search
            + Ask for and save user's Zotero API info
            + Ask for and save user's export preferences

        """
        Zotero(self.wf).set_api()
        ZotQuery(self.wf).set_output()


def main(wf):
    """Accept Alfred's args and pipe to proper Class"""

    ZotWorkflow(wf).do_config()

    

if __name__ == '__main__':
    WF = Workflow()
    log = WF.logger
    decode = WF.decode
    sys.exit(WF.run(main))
