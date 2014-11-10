#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

# Standard Library
import os
import struct
import sqlite3
import os.path
from time import time
from shutil import copyfile
from collections import OrderedDict

# Internal Dependencies
import utils
import config
from lib import pashua
from zotero import zot
from config import PropertyBase, stored_property

# Alfred-Workflow
from workflow import Workflow

# create global methods from `Workflow()`
WF = Workflow()
log = WF.logger
decode = WF.decode
fold = WF.fold_to_ascii


#------------------------------------------------------------------------------
# :class:`ZotQuery` -----------------------------------------------------------
#------------------------------------------------------------------------------

class ZotqueryBackend(PropertyBase):
    """Contains all relevant information about this workflow.

    |       Key       |                 Description                  |
    |-----------------|----------------------------------------------|
    | `cloned_sqlite` | ZotQuery's clone of Zotero's sqlite database |
    | `json_data`     | ZotQuery's JSON clone of Zotero's sqlite     |
    | `fts_sqlite`    | ZotQuery's Full Text Search database         |
    | `folded_sqlite` | ZotQuery's ASCII-only FTS database           |

    Expects information to be stored in :file:`zotquery_data.json`.
    If file does not exist, it creates and stores dictionary.

    """
    def __init__(self, wf):
        """Initialize class instance.

        :param wf: a new :class:`Workflow` instance.
        :type wf: :class:`object`
        """
        self.wf = wf
        # initialize :class:`LocalZotero`
        self.zotero = zot(self.wf)
        # initialize base class, for access to `properties` dict
        PropertyBase.__init__(self, self.wf, secured=False)
        self.con = None

    # Properties --------------------------------------------------------------

    @stored_property
    def cloned_sqlite(self):
        """Return path to ZotQuery's cloned sqlite database.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        clone_path = self.wf.datafile('zotquery.sqlite')
        if not os.path.exists(clone_path):
            copyfile(self.zotero.original_sqlite, clone_path)
            log.info('Created Clone SQLITE file')
        return clone_path

    @stored_property
    def json_data(self):
        """Return path to ZotQuery's JSON version of user's Zotero database.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        json_path = self.wf.datafile('zotquery.json')
        if not os.path.exists(json_path):
            self.con = sqlite3.connect(self.cloned_sqlite)
            # Function to generate ZotQuery's JSON database
            self.to_json()
        return json_path

    @stored_property
    def fts_sqlite(self):
        """Return path to ZotQuery's Full Text Search sqlite database.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        fts_path = self.wf.datafile('zotquery.db')
        if not os.path.exists(fts_path):
            self.create_index_db(fts_path)
            self.update_index_db(fts_path)
        return fts_path

    @stored_property
    def folded_sqlite(self):
        """Return path to ZotQuery's Full Text Search sqlite database
        where all text is ASCII only.

        :returns: full path to file
        :rtype: :class:`unicode`

        """
        folded_path = self.wf.datafile('folded.db')
        if not os.path.exists(folded_path):
            self.create_index_db(folded_path)
            self.update_index_db(folded_path, folded=True)
        return folded_path

    # ZotQuery Formatting Properties ------------------------------------------

    @stored_property
    def zotero_app(self):
        return self.check_storage('app',
                                  self.formatting_properties_setter)

    @stored_property
    def csl_style(self):
        return self.check_storage('csl',
                                  self.formatting_properties_setter)

    @stored_property
    def output_format(self):
        return self.check_storage('fmt',
                                  self.formatting_properties_setter)

    def formatting_properties_setter(self):
        """Configure ZotQuery formatting perferences."""
        # Check if values have already been set
        defaults = self.wf.cached_data('output_settings', max_age=0)
        if defaults is None:
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
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=config.PASHUA)
        if res_dict['cb'] != 1:
            del res_dict['cb']
            self.wf.cache_data('output_settings', res_dict)

    # Utility methods ---------------------------------------------------------

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
        clone_path = self.wf.datafile('zotquery.sqlite')
        copyfile(self.zotero.original_sqlite, clone_path)
        log.info('Updated Clone SQLITE file')

    def update_json(self):
        """Update `json_data` so that it's current with `cloned_sqlite`.

        """
        self.con = sqlite3.connect(self.cloned_sqlite)
        # backup previous version of library
        if os.path.exists(self.json_data):
            copyfile(self.json_data, self.wf.datafile('backup.json'))
        # update library
        self.to_json()
        log.info('Updated and backed-up JSON file')

    ## JSON to FTS sub-methods ------------------------------------------------

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
            columns = config.FILTERS.get('general', None)
            if columns:
                # convert list to string
                columns = ', '.join(columns)
                sql = """CREATE VIRTUAL TABLE zotquery
                         USING fts3({cols})""".format(cols=columns)
                cur.execute(sql)
                log.debug('Created FTS database: {}'.format(db))

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
                # names of all keys for item (cf. `FILTERS['general']`)
                columns = ', '.join([x.keys()[0] for x in row])
                values = ['"' + x.values()[0].replace('"', "'") + '"'
                          for x in row]
                values = ', '.join(values)
                # fold to ASCII-only?
                if folded:
                    values = fold(values)
                sql = """INSERT OR IGNORE INTO zotquery
                         ({columns}) VALUES ({data})
                        """.format(columns=columns, data=values)
                cur.execute(sql)
                count += 1
        log.debug('Added/Updated {} items in {:0.3}s'.format(count,
                                                             time() - start))

    def generate_data(self):
        """Create a genererator with dictionaries for each item
        in ``json_data``.

        :returns: ``list`` of ``dicts`` with all item's data as ``strings``
        :rtype: :class:`genererator`

        """
        json_data = utils.read_json(self.json_data)
        # for each `item`, get its data in dict format
        for item in json_data.itervalues():
            array = list()
            # get search columns from scope
            columns = config.FILTERS.get('general', None)
            if columns:
                for column in columns:
                    # get search map from column
                    json_map = config.FILTERS_MAP.get(column, None)
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
            elif isinstance(val_map[0], list):  # list of possible k, v pairs
                check = None
                for pair in val_map:
                    [key, val] = pair
                    try:
                        check = [item[key][val]]
                    except KeyError:
                        pass
                result = check if check else []
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
            machine byte order (see http://www.sqlite.org/fts3.html#matchinfo)
            and `struct` defaults to machine byte order.
            """
            bufsize = len(matchinfo)  # Length in bytes.
            matchinfo = [struct.unpack(b'I', matchinfo[i:i + 4])[0]
                         for i in range(0, bufsize, 4)]
            it = iter(matchinfo[2:])
            return sum(x[0] * w / x[1]
                       for x, w in zip(zip(it, it, it), weights)
                       if x[1])
        return rank

    ## SQLITE to JSON sub-methods ---------------------------------------------

    # TODO: Create a JSON db class to house all this code
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
        # get key data for each Zotero item
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
            if config.PERSONAL_ONLY is True and library_id is not None:
                continue
            library_id = library_id if library_id is not None else '0'
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
        log.info('Created JSON file in {:0.3}s'.format(time() - start))

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

    ### Individual Item Data --------------------------------------------------

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
            if _attachment[0]:
                (att_path,
                 attachment_id) = _attachment
                # if internal attachment
                if att_path[:8] == "storage:":
                    att_path = att_path[8:]
                    # if right kind of attachment
                    if True in (att_path.endswith(ext) for ext in config.ATTACH_EXTS):
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
                    if True in (att_path.endswith(ext) for ext in config.ATTACH_EXTS):
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

#-----------------------------------------------------------------------------
# Alias
#-----------------------------------------------------------------------------

data = ZotqueryBackend
