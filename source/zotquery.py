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

"""zotquery.py -- Zotero interface for Alfred

Usage:

    zotquery.py uses bash-style flags to specify object classes, 
    followed by one or more args necessary for that object.

    zotquery.py --cache <force> <personal_only>
        type <force> = Boolean
        vals <force>:
            True = update cache regardless of freshness
            False = update cache only if `zotero.sqlite` has changed
        type <personal_only> = Boolean
        vals <personal_only>:
            True = restrict cached data to user's personal Zotero library
            False = cache all data (personal and group libraries)

    zotquery.py --config <method>
        type <method> = string
        vals <method>:
            'api' = Setup/update user's Zotero API data
            'prefs' = Setup/update user's export preferences
            'paths' = Setup paths to user's key Zotero directories

    zotquery.py --filter <query> <scope>
        type <query> = string
        vals <query>: any
        type <scope> = string
        vals <scope>:
            'general' = search against all relevant item data
            'titles' = search against item's title and collection title
            'creators' = search against item's creators' last names
            'collections' = search for a collection
            'tags' = search for a tag
            'notes' = search against item's notes
            'attachments' = search against item's attachments
            'in-collection' = search within saved coll using `general` scope
            'in-tag' = search within saved tag using `general` scope
            'debug' = list ZotQuery's directories
            'new' = list item's added since last cache update

    zotquery.py --action <key> <command>
        type <key> = string
        vals <key> = item's Zotero key
        type <command> = string
        vals <command>:
            'cite' = copy full citation of item to clipboard
            'ref' = copy short reference of item to clipboard
            'cite_group' = copy full bibliography of collection/tag to clipboard
            'append' = append full citation of item to temporary bibliography
            'save_coll' = save name of chosen collection to temporary file 
                (for `in-collection` filter)
            'save_tag' = save name of chosen tag to temporary file
                (for `in-tag` filter)
            'att' = open item's attachment in default app
            'bib' = copy temporary bibliography to clipboard
            'open' = open item in Zotero client
"""

# Standard Library
import re
import sys
import json
import shutil
import os.path
import sqlite3
import subprocess
from collections import OrderedDict

# Dependencies
DEPS = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'deps')
# Use bundler for external dependencies
import bundler
bundler.init()
import html2text
from pyzotero import zotero
from workflow import Workflow
from workflow.workflow import MATCH_ALL, MATCH_ALLCHARS

__version__ = '0.9'

# Path to apps
STANDALONE = os.path.expanduser('~/Library/Application Support/Zotero/')
FIREFOX = os.path.expanduser('~/Library/Application Support/Firefox/')
ATTACHMENT_EXTS = [".pdf", "epub"]      # Needs to be 4 chars long


###############################################################################
# Helper functions                                                            #
###############################################################################

def unify(text, encoding='utf-8'):
    """Convert `text` to unicode"""

    # https://github.com/kumar303/unicode-in-python/blob/master/unicode.txt
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return text

def boolify(text):
    """Convert string to Boolean"""

    if str(text).lower() in ('true', 't', '1'):
        return True
    elif str(text).lower() in ('false', 'f', '0'):
        return False

def applescriptify(text):
    """Replace double quotes in `text` for Applescript"""

    uni_str = unify(text)
    return uni_str.replace('"', '" & quote & "')

def run_applescript(scpt_str):
    """Run an applescript"""

    process = subprocess.Popen(['osascript', '-e', scpt_str],
                                stdout=subprocess.PIPE)
    out = process.communicate()[0]
    return out.strip()
 
def set_clipboard(data):
    """Set clipboard to `data`"""

    encoded_str = unify(data).encode('utf-8')
    scpt_str = 'set the clipboard to "{0}"'.format(applescriptify(encoded_str))
    run_applescript(scpt_str)

def make_query(_list):
    """Prepare SQLITE query string"""

    [_sel, _src, _mtch, _id] = _list
    sql = """SELECT {sel} FROM {src} WHERE {mtch} = {id}"""
    query = sql.format(sel=_sel, src=_src, mtch=_mtch, id=_id)
    return query

def html2rtf(html_path):
    """Convert html to RTF and copy to clipboard"""
    scpt_str = """
        do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
        """.format(applescriptify(html_path))
    run_applescript(scpt_str)
    return True

###############################################################################
# Cache Object                                                                #
###############################################################################

class ZotCache(object):
    """Caching Object"""

    def __init__(self, force, personal_only):
        self.force = force
        self.personal_only = personal_only
        self.wf_obj = Workflow()
        # Get various databases
        self.zot_db = self.get_path('database_path')
        self.clone_db = self.wf_obj.datafile("zotquery.sqlite")
        self.db_json = self.wf_obj.datafile("zotero_db.json")
        self.backup_json = self.wf_obj.datafile("old_db.json")

        if os.path.exists(self.clone_db):
            self.conn = sqlite3.connect(self.clone_db)
        else:
            self.conn = sqlite3.connect(self.zot_db)


    ###########################################################################
    ### Setup Methods                                                       ###
    ###########################################################################

    def setup(self):
        """Ensure configuration and create copies"""

        if os.path.exists(self.wf_obj.datafile("first-run.txt")):
            # Back-up old Cache
            if os.path.exists(self.db_json):
                shutil.copyfile(self.db_json, 
                                self.backup_json)
            # Begin new cache?
            if self.force or self.check_cache()[0]:     
                shutil.copyfile(self.zot_db, self.clone_db)
                return True
            else:
                return False
        else: # Not configured
            scpt_str = 'tell application "Alfred 2" to search "z:config"'
            run_applescript(scpt_str)
            return False

    def get_path(self, path): 
        """Get `path` val from paths.json file in Alfred non-volatile storage"""

        with open(self.wf_obj.datafile("paths.json"), 'r') as file_obj:
            paths_dct = json.load(file_obj)
            file_obj.close()
        return unify(paths_dct[path])

    def check_cache(self):
        """Does the cache need to be updated?"""

        [update, spot] = [False, None]
        zotero_mod = os.stat(self.get_path('database_path'))[8]
        clone_mod = os.stat(self.wf_obj.datafile('zotquery.sqlite'))[8]
        cache_mod = os.stat(self.wf_obj.datafile('zotero_db.json'))[8]
        # Check if cloned .sqlite database is up-to-date with Zotero database
        if zotero_mod > clone_mod:
            [update, spot] = [True, "Clone"]
        # Check if JSON cache is up-to-date with the cloned database
        if (cache_mod - clone_mod) > 10:
            [update, spot] = [True, "JSON"]
        return [update, spot]


    ###########################################################################
    ### SQLite Methods                                                      ###
    ###########################################################################

    def sqlite_get(self, _sql):
        """Retrieve data from Zotero sqlite database"""

        cur = self.conn.cursor() 
        _info = cur.execute(_sql)
        return _info

    def sqlite_close(self):
        """Close connection to database"""

        self.conn.close()

    def query(self, sql_obj):
        """Pass `sql_obj` to query string and return results"""

        sql_query = make_query(sql_obj) 
        return self.sqlite_get(sql_query)


    ###########################################################################
    ### SQLite Methods                                                      ###
    ###########################################################################

    def info_query(self):
        """Retrieve (key, id, type id) from item"""

        info_sql = """SELECT key, itemID, itemTypeID, libraryID
            FROM items
            WHERE 
                itemTypeID not IN (1, 13, 14)
            ORDER BY dateAdded DESC"""
        return self.sqlite_get(info_sql)

    def creator_query(self, creator_data_id, creator_type_id):
        """Retrieve (last name, first name, type) from item"""

        creator_info_sql = """SELECT creatorData.lastName, 
            creatorData.firstName, creatorTypes.creatorType 
            FROM creatorData, creatorTypes
            WHERE
                creatorDataID = {0}
                and creatorTypeID = {1}""".format(creator_data_id, 
                                                  creator_type_id)
        return self.sqlite_get(creator_info_sql)

    def collection_query(self, coll_id):
        """Retrieve (collection name, collection key) from item"""

        collection_info_sql = """SELECT collectionName, key
            FROM collections
            WHERE 
                collectionID = {0}
                and libraryID is null""".format(coll_id)
        return self.sqlite_get(collection_info_sql)

    def group_query(self, coll_id):
        """Retrieve (coll name, coll key, group name, group id) from item"""

        group_info_sql = """SELECT collections.collectionName,
            collections.key, groups.name, groups.libraryID
            FROM collections, groups
            WHERE 
                collections.collectionID = {0}
                and collections.libraryID is not null""".format(coll_id)
        return self.sqlite_get(group_info_sql)  
    

    ############################################################################
    ### Cache Methods                                                        ###
    ############################################################################

    def cache(self):
        """Update cache if neccessary"""

        if self.setup():
            json_cache = self.get_cache()

            with open(self.wf_obj.datafile("zotero_db.json"), 'w') as file_:
                file_.write(json_cache.encode('utf-8'))
                file_.close()
            return "Cache Updated!"
        else:
            return "Cache up-to-date."

    def get_cache(self):
        """Convert Zotero .sqlite database to JSON file"""

        # adapted from:
        # https://github.com/pkeane/zotero_hacks
        _items = []
        basic_info = self.info_query()

        for basic in basic_info:
            # prepare item's base dict and data dict
            item_dict = OrderedDict()
            item_meta = OrderedDict()

            item_key = item_id = item_type_id = library_id = ''
            (item_key,
             item_id,
             item_type_id,
             library_id) = basic

            # If user only wants personal library
            if self.personal_only == True and library_id != None:
                continue

            item_dict['key'] = item_key
            if library_id == None: 
                library_id = '0'
            item_dict['library'] = unify(library_id)

            type_name = ''
            type_query = ['typeName', 'itemTypes', 'itemTypeID', item_type_id]
            (type_name,) = self.query(type_query).fetchone()
            item_dict['type'] = type_name

            ##### Creators Info
            item_dict['creators'] = []
            creators_query = ['creatorID, creatorTypeID, orderIndex',
                              'itemCreators', 'itemID', item_id]
            creators_data = self.query(creators_query)
            for _creator in creators_data:
                creator_id = creator_type_id = creator_id = order_index = ''
                (creator_id, 
                 creator_type_id, 
                 order_index) = _creator
                creators_id_query = ['creatorDataID', 'creators',
                                    'creatorID', creator_id]
                (creator_data_id,) = self.query(creators_id_query).fetchone()
                creators_info = self.creator_query(creator_data_id, 
                                                        creator_type_id)
                for creator_info in creators_info:
                    first_name = last_name = ''
                    (last_name, 
                     first_name, 
                     c_type) = creator_info
                    item_dict['creators'].append({'family': last_name, 
                                                  'given': first_name, 
                                                  'type': c_type, 
                                                  'index': order_index})
            ##### Meta-Data Info
            metadata_id_query = ['fieldID, valueID',
                                 'itemData', 'itemID', item_id]
            items_data = self.query(metadata_id_query)
            for _item in items_data:
                field_id = value_id = value_name = ''
                (field_id, 
                 value_id) = _item
                field_name_query = ['fieldName', 'fields', 'fieldID', field_id]
                (field_name,) = self.query(field_name_query).fetchone()
                if field_name not in item_meta:
                    item_meta[field_name] = ''
                    value_name_query = ['value', 'itemDataValues',
                                        'valueID', value_id]
                    (value_name,) = self.query(value_name_query).fetchone()
                    if field_name == 'date':
                        item_meta[field_name] = unify(value_name[0:4])
                    else:
                        item_meta[field_name] = unify(value_name)
            item_dict['data'] = item_meta
            
            ##### Collection Info
            item_dict['zot-collections'] = []
            coll_id_query = ['collectionID', 'collectionItems',
                                   'itemID', item_id]
            collections_data = self.query(coll_id_query)
            for _collection in collections_data:
                coll_id = ''
                (coll_id,) = _collection
                collection_info = self.collection_query(coll_id).fetchall()
                if collection_info != []:
                    (collection_name, 
                     collection_key) = collection_info[0]
                    item_dict['zot-collections'].append(
                                                    {'name': collection_name,
                                                    'key': collection_key,
                                                    'library_id': '0',
                                                    'group': 'personal'})
                else:
                    if self.personal_only == False:
                        (collection_name, 
                        collection_key, 
                        group_name, 
                        library_id) = self.group_query(coll_id).fetchone()
                        item_dict['zot-collections'].append(
                                                    {'name': collection_name,
                                                    'key': collection_key,
                                                    'library_id': library_id,
                                                    'group': group_name})
            ##### Tag Info
            item_dict['zot-tags'] = []
            tag_id_query = ['tagID', 'itemTags', 'itemID', item_id]
            tags_data = self.query(tag_id_query)
            for _tag in tags_data:
                tag_id = ''
                (tag_id,) = _tag
                tag_info_query = ['name, key', 'tags', 'tagID', tag_id]
                (tag_name,
                 tag_key) = self.query(tag_info_query).fetchone()
                item_dict['zot-tags'].append({'name': tag_name,
                                            'key': tag_key})
            ##### Attachment Info
            item_dict['attachments'] = []
            attachment_info_query = ['path, itemID', 'itemAttachments',
                                     'sourceItemID', item_id]
            attachments_data = self.query(attachment_info_query)
            for _attachment in attachments_data:
                if _attachment[0] != None:
                    (att_path, 
                        attachment_id) = _attachment
                    if att_path[:8] == "storage:":
                        att_path = att_path[8:]
                        if att_path[-4:].lower() in ATTACHMENT_EXTS:
                            att_query = ['key', 'items',
                                         'itemID', attachment_id]
                            (att_key,) = self.query(att_query).fetchone()
                            storage_path = self.get_path('storage_path')
                            base_path = os.path.join(storage_path,
                                                     att_key)
                            final_path = os.path.join(base_path,
                                                      att_path)
                            item_dict['attachments'].append({'name': att_path,
                                                            'key': att_key,
                                                            'path': final_path})
                    elif att_path[:12] == "attachments:":
                        att_path = att_path[12:]
                        if att_path[-4:].lower() in ATTACHMENT_EXTS:
                            att_query = ['key', 'items',
                                         'itemID', attachment_id]
                            (att_key,) = self.query(att_query).fetchone()
                            base = self.get_path('link-attachments_path')
                            final_path = os.path.join(base, att_path)
                            item_dict['attachments'].append({'name': att_path,
                                                        'key': att_key,
                                                        'path': final_path})
                    else:
                        attachment_name = att_path.split('/')[-1]
                        item_dict['attachments'].append(
                                                    {'name': attachment_name,
                                                    'key': None,
                                                    'path': att_path})
            ##### Notes Info
            item_dict['notes'] = []
            note_info_query = ['note', 'itemNotes', 'sourceItemID', item_id]
            notes_data = self.query(note_info_query)
            for _note in notes_data:
                note = ''
                (note,) = _note
                item_dict['notes'].append(note[33:-10])
            ##### Add item dict to running list
            _items.append(item_dict)

        final_json = json.dumps(_items, 
                                sort_keys=False, 
                                indent=4, 
                                separators=(',', ': '))
        self.sqlite_close()

        return final_json



###############################################################################
# Config Class                                                                #
###############################################################################

class ZotConfig(object):
    """Configurator Object"""

    def __init__(self, scope):
        self.scope = scope
        self.wf_obj = Workflow()
        self.api_scpt = os.path.join(DEPS, 'config_zotero-api.scpt')
        self.pref_scpt = os.path.join(DEPS, 'config_export-pref.scpt')
        self.ui_scpt = os.path.join(DEPS, '_ui-helpers.scpt')

        if not os.path.exists(self.wf_obj.datafile('zot_filters.json')):
            self.zot_string_prefs()

    ###########################################################################
    ### Primary API Method                                                  ###
    ###########################################################################

    def config(self):
        """Call proper config action"""

        if self.scope == 'api':
            return self.set_api_data()
        elif self.scope == 'prefs':
            return self.set_export_prefs()
        elif self.scope == 'paths':
            return self.set_zot_paths()

    ###########################################################################
    ### Config Methods                                                      ###
    ###########################################################################
 
    def set_api_data(self):
        """Save Zotero API info to `settings.json` file"""

        process = subprocess.Popen(['osascript', self.api_scpt],
                                    stdout=subprocess.PIPE)
        out = process.communicate()[0]
        return out.strip()

    def set_export_prefs(self):
        """Save export prefs to `prefs.json` file"""

        process = subprocess.Popen(['osascript', self.pref_scpt],
                                    stdout=subprocess.PIPE)
        out = process.communicate()[0]
        return out.strip()

    def set_zot_paths(self):
        """Save paths to key Zotero items to `paths.json` file"""

        # Path to preferences files
        zs_pref_path = self._get_profile(STANDALONE) + '/prefs.js'
        zf_pref_path = self._get_profile(FIREFOX) + '/prefs.js'

        if os.path.exists(STANDALONE):
            default_path = STANDALONE
        elif os.path.exists(FIREFOX):
            default_path = STANDALONE
        else:
            default_path = os.path.expanduser('~/Library/Application Support/')

        data_path = attach_path = ''
        if self._get_paths(zf_pref_path)[0]:
            data_path = self._get_paths(zf_pref_path)[0]
            default_path = zf_pref_path
        elif self._get_paths(zs_pref_path)[0]:
            data_path = self._get_paths(zs_pref_path)[0]
            default_path = zs_pref_path
        storage_path = os.path.join(data_path, 'storage')
        db_path = os.path.join(data_path, 'zotero.sqlite')

        if self._get_paths(zf_pref_path)[1]:
            attach_path = self._get_paths(zf_pref_path)[1]
        elif self._get_paths(zs_pref_path)[1]:
            attach_path = self._get_paths(zs_pref_path)[1]

        # Check if prefs paths exist
        if not os.path.exists(storage_path): 
            scpt_str = """
                set ui to load script POSIX file "{0}"
                set prompt to "Select Zotero storage folder."
                ui's choose_folder({{z_prompt:prompt, z_def:"{1}"}})
            """.format(self.ui_scpt, default_path)
            storage_path = run_applescript(scpt_str)

        if not os.path.exists(db_path):
            scpt_str = """
                set ui to load script POSIX file "{0}"
                set prompt to "Select Zotero sqlite database."
                ui's choose_file({{z_prompt:prompt, z_def:"{1}"}})
            """.format(self.ui_scpt, default_path)
            db_path = run_applescript(scpt_str)

        if not os.path.exists(attach_path): 
            scpt_str = """
                set ui to load script POSIX file "{0}"
                set prompt to "Select Zotero folder for linked attachments."
                set the_path to (POSIX path of (path to documents folder))
                ui's choose_folder({{z_prompt:prompt, z_def:the_path}})
            """.format(self.ui_scpt)
            attach_path = run_applescript(scpt_str)

        _dict = {'storage_path': storage_path, 
                 'database_path': db_path, 
                 'link-attachments_path': attach_path}
        _json = json.dumps(_dict, 
                            sort_keys=False, 
                            indent=4, 
                            separators=(',', ': '))
        # Store the paths in non-volatile storage
        with open(self.wf_obj.datafile("paths.json"), 'w') as file_obj:
            file_obj.write(_json.encode('utf-8'))
            file_obj.close()
        
        return "Zotero paths saved!"

    ###########################################################################
    ### Helper Functions                                                    ###
    ###########################################################################

    def _get_profile(self, root):
        """Read the Zotero profiles.ini file from `root`"""

        profile_path = root + 'profiles.ini'
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as file_obj:
                data_str = file_obj.read()
                file_obj.close()
            partial_path = re.search(r"(?<=^Path=)(.*?)$", data_str, re.M)
            full_path = root + partial_path.group()
            return unify(full_path)
        else:
            return 'None'

    def _get_paths(self, prefs):
        """Search `prefs` file for all data paths"""

        last_data_dir_re = re.compile(r"""
            user_pref\("extensions\.zotero\.lastDataDir",\s"(.*?)"\);
            """.strip())
        data_dir_re = re.compile(r"""
            user_pref\(\"extensions\.zotero\.dataDir\",\s\"(.*?)\"\);
            """.strip())
        base_dir_re = re.compile(r"""
            user_pref\(\"extensions\.zotero\.baseAttachmentPath\",\s\"(.*?)\"\);
            """.strip())

        if os.path.exists(prefs):
            with open(prefs, 'r') as file_obj:
                _prefs = file_obj.read()
                file_obj.close()
            # Get path to data directory
            data_dir = re.search(last_data_dir_re, _prefs)
            try:
                data_path = data_dir.group(1)
            except AttributeError:
                try:
                    data_dir = re.search(data_dir_re, _prefs)
                    data_path = data_dir.group(1)
                except AttributeError:
                    data_path = None
            # Get path to directory for linked attachments
            attach_dir = re.search(base_dir_re, _prefs)
            try:    
                attach_path = attach_dir.group(1)
            except AttributeError:
                attach_path = None
            return [data_path, attach_path]
        else:
            return [False, False]

    def zot_string_prefs(self):
        """Ensure prefs for `zot_string` function exist"""
        zot_string_prefs = {'general': [
                                ['data', 'title'],
                                ['creators', 'family'],
                                ['data', 'publicationTitle'],
                                ['data', 'bookTitle'],
                                ['data', 'proceedingsTitle'],
                                ['data', 'date'],
                                ['zot-collections', 'name'],
                                ['zot-tags', 'name'],
                                ['notes']],
                            'titles': [
                                ['data', 'title'],
                                ['data', 'publicationTitle'],
                                ['data', 'bookTitle'],
                                ['data', 'proceedingsTitle'],
                                ['data', 'date']],
                            'creators': [
                                ['creators', 'family'],
                                ['data', 'date']],
                            'in-collection': [
                                ['zot-collections', 'name']],
                            'attachments': [
                                ['attachments', 'name']],
                            'in-tag': [
                                ['zot-tags', 'name']],
                            'notes': [
                                ['notes']]
                            }
        _json = json.dumps(zot_string_prefs, 
                           sort_keys=False, 
                           indent=4, 
                           separators=(',', ': '))
        with open(self.wf_obj.datafile('zot_filters.json'), 'w') as file_obj:
            file_obj.write(_json)
            file_obj.close()



###############################################################################
# Filter Class                                                                #
###############################################################################

class ZotFilter(object):
    """Filtering Object"""

    def __init__(self, query, scope, personal_only=False,
                 test_data=None, test_group=None):
        self.wf_obj = Workflow()
        self.query = query
        self.scope = scope

        if self.first_run_test() and self.query_len_test(): 
            pass   
        if test_data == None:
            with open(self.wf_obj.datafile("zotero_db.json"), 'r') as file_obj:
                self.data = json.load(file_obj)
                file_obj.close()
            if personal_only == True:
                personal_data = []
                keys = []
                for i in self.data:
                    if i['zot-collections'] != []:
                        for coll in i['zot-collections']:
                            if coll['group'] == 'personal':
                                if not i['key'] in keys:
                                    personal_data.append(i)
                                    keys.append(i['key'])
                self.data = personal_data
        else:
            self.data = test_data

        if test_group != None:
            self.filters_in_groups(test_group)

    
    ###########################################################################
    ### Primary API Method                                                  ###
    ###########################################################################

    def filter(self):
        """Main API method"""

        if self.scope in ['general', 'creators', 'titles', 'notes']:
            self.filters_simple()
        elif self.scope in ['collections', 'tags']:
            self.filters_groups()
        elif self.scope in ['in-collection', 'in-tag']:
            self.filters_in_groups()
        elif self.scope == 'attachments':
            self.filter_atts()
        elif self.scope == 'debug':
            return self.filter_debug()
        elif self.scope == 'new':
            return self.filter_new()

    ############################################################################
    ### Sub-Methods                                                          ###
    ############################################################################

    def filters_simple(self):
        """Simple Filter method"""

        filtered_lst = self.wf_obj.filter(self.query, self.data, 
                            key=lambda x: self.zot_string(x, self.scope),
                            match_on=MATCH_ALL ^ MATCH_ALLCHARS) 
        if filtered_lst != []:
            # Format matched items for display
            prep_res = self.prepare_feedback(filtered_lst)  
            for item in prep_res:
                self.wf_obj.add_item(**item) # Pass pre-formatted `dict`
            self.wf_obj.send_feedback()
        else:
            self.no_results()

    def filters_groups(self):
        """Group Filter method"""

        res_dict = self._get_group_data()
        if res_dict['data'] != []:
            filtered_lst = self.wf_obj.filter(self.query, res_dict['data'],
                                key=lambda x: x[0],
                                match_on=MATCH_ALL ^ MATCH_ALLCHARS)
            if filtered_lst != []:
                if self.scope == "collections":
                    _pre = "c:"
                elif self.scope == "tags":
                    _pre = "t:"
                for item in filtered_lst:
                    self.wf_obj.add_item(item[0], res_dict['sub'], 
                        arg=_pre + item[1], 
                        valid=True, 
                        icon=res_dict['icon'])
                self.wf_obj.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filters_in_groups(self, test_group=None):
        """In-Group Filter method"""

        res_lst = self._get_ingroup_data(test_group)
        if res_lst != []:
            filtered_lst = self.wf_obj.filter(self.query, res_lst, 
                                key=lambda x: self.zot_string(x, 'general'),
                                match_on=MATCH_ALL ^ MATCH_ALLCHARS)
            if filtered_lst != []:
                prep_res = self.prepare_feedback(filtered_lst)  
                for item in prep_res:
                    self.wf_obj.add_item(**item) # Pass pre-formatted `dict`
                self.wf_obj.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filter_atts(self):
        """Attachments Filter method"""

        res_lst = self._get_atts_data()
        if res_lst != []:
            filtered_lst = self.wf_obj.filter(self.query, res_lst, 
                                key=lambda x: self.zot_string(x, 'general'),
                                match_on=MATCH_ALL ^ MATCH_ALLCHARS)
            if filtered_lst != []:
                for item in filtered_lst:
                    info = self.info_format(item)
                    title = item['data']['title']
                    sub = info[0] + ' ' + info[1]
                    self.wf_obj.add_item(title, sub, 
                        arg=item['attachments'][0]['path'], 
                        valid=True,
                        type='file',
                        icon='icons/n_pdf.png')
                self.wf_obj.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filter_debug(self):
        """Debug options Filter method"""

        self.wf_obj.add_item("Root", "Open ZotQuery's Root Folder?", 
            valid=True, 
            arg='workflow:openworkflow', 
            icon='icons/n_folder.png')
        self.wf_obj.add_item("Storage", "Open ZotQuery's Storage Folder?", 
            valid=True, 
            arg='workflow:opendata', 
            icon='icons/n_folder.png')
        self.wf_obj.add_item("Cache", "Open ZotQuery's Cache Folder?", 
            valid=True, 
            arg='workflow:opencache', 
            icon='icons/n_folder.png')
        self.wf_obj.add_item("Logs", "Open ZotQuery's Logs?", 
            valid=True, 
            arg='workflow:openlog', 
            icon='icons/n_folder.png')
        self.wf_obj.send_feedback()

    def filter_new(self):
        """New items Filter method"""

        curr_keys = [item['key'] for item in self.data]
        # Get previous Zotero data from JSON cache
        with open(self.wf_obj.datafile('old_db.json'), 'r') as file_obj:
            old_data = json.load(file_obj)
            file_obj.close()
        old_keys = [item['key'] for item in old_data]
        # Get list of newly added items
        new_keys = list(set(curr_keys) - set(old_keys))
        new_items = [item for item in self.data if item['key'] in new_keys]
        if new_items != []:
            prep_res = self.prepare_feedback(new_items)
            for item in prep_res:
                self.wf_obj.add_item(**item) # Pass pre-formatted `dict`
            self.wf_obj.send_feedback()
        else:
            self.wf_obj.add_item("No new items!",
                    "You have not added any new items to your Zotero library.", 
                    icon="icons/n_error.png")
            self.wf_obj.send_feedback()

    ###########################################################################
    ### Get sub-sets of data methods                                        ###
    ###########################################################################

    def _get_group_data(self):
        """Sub-Method for Group data"""

        conn = sqlite3.connect(self.wf_obj.datafile("zotquery.sqlite"))
        cur = conn.cursor()
        if self.scope == "collections":
            sql_query = """SELECT collectionName, key
                FROM collections"""
            _sub = "Collection"
            _icon = "icons/n_collection.png"
        elif self.scope == "tags":
            sql_query = """SELECT name, key
                FROM tags"""
            _sub = "Tag"
            _icon = "icons/n_tag.png"
        group_data = cur.execute(sql_query).fetchall()
        conn.close()
        return {'data': group_data,
                'sub': _sub,
                'icon': _icon}

    def _get_ingroup_data(self, test_group):
        """Sub-Method for In-Group data"""

        term = self.scope.split('-')[1]
        if test_group == None:
            path = self.wf_obj.cachefile("{0}_query_result.txt").format(term)
            with open(path, 'r') as file_obj:
                inp_str = unify(file_obj.read())
                file_obj.close()
            inp_key = inp_str.split(':')[1]
        else:
            inp_key = test_group

        items = []
        for item in self.data:
            for jtem in item['zot-{0}s'.format(term)]:
                if inp_key == jtem['key']: 
                    items.append(item)
        return items
    
    def _get_atts_data(self):
        """Sub-Method for Attachments data"""

        items = []
        for item in self.data:
            if item['attachments'] != []:
                items.append(item)
        return items

    ###########################################################################
    ### Helper Functions                                                    ###
    ###########################################################################

    def first_run_test(self):
        """Check if workflow is configured"""

        if not os.path.exists(self.wf_obj.datafile("first-run.txt")):
            scpt_str = 'tell application "Alfred 2" to search "z:config"'
            run_applescript(scpt_str)
        else: return True

    def query_len_test(self):
        """Check if query terms have enough letters"""

        if len(self.query) <= 2:
            self.wf_obj.add_item("Error!", 
                "Need at least 3 letters to execute search", 
                icon="icons/n_delay.png")
            self.wf_obj.send_feedback()
            sys.exit(0)
        else: return True

    def no_results(self):
        """Return no results"""

        self.wf_obj.add_item("Error!", "No results found.", 
                        icon="icons/n_error.png")
        self.wf_obj.send_feedback()
        sys.exit(0)

    def get_datum(self, _item, pair):
        """Retrieve value from item as list"""

        try:
            [key, val] = pair
            try:
                return [_item[key][val]]
            except TypeError:
                return [x[val] for x in _item[key]]
        except ValueError:
            [key] = pair
            return _item[key]
        except:
            return []

    def zot_string(self, _item, scope='general'):
        """Convert key values of item into string for fuzzy filtering"""

        with open(self.wf_obj.datafile('zot_filters.json')) as file_obj:
            filters = json.load(file_obj)
            file_obj.close()

        _list = []
        for key, val in filters.items():
            if key == scope:
                for pair in val:
                    _list += self.get_datum(_item, pair)
        
        _list = [unicode(x) for x in _list]
        _str = ' '.join(_list)
        return unify(_str)

    def prepare_feedback(self, results):
        """Prepare dictionary for workflow results"""

        xml_lst = []
        ids = []
        for item in results:
            if item['key'] not in ids:
                ids.append(item['key'])
                # Format the Zotero match results
                info = self.info_format(item)
                # Prepare data for Alfred
                _title = item['data']['title']
                _sub = info[0] + ' ' + info[1]
                _pre = 'n'
                _arg = str(item['library']) + '_' + str(item['key'])
                # Create dictionary of necessary Alred result info.
                # For Alfred to remember results, add 'uid': str(item['id'])
                dct = {'title': _title, 'subtitle': _sub, 
                            'valid': True, 'arg': _arg}
                # If item has an attachment
                if item['attachments'] != []:
                    _pre = 'att'
                    dct.update({'subtitle': _sub + ' Attachments: ' 
                                    + str(len(item['attachments']))})
                # Export items to Alfred xml with appropriate icons
                if item['type'] == 'journalArticle':
                    dct.update({'icon': 'icons/{}_article.png'.format(_pre)})
                elif item['type'] == 'book':
                    dct.update({'icon': 'icons/{}_book.png'.format(_pre)})
                elif item['type'] == 'bookSection':
                    dct.update({'icon': 'icons/{}_chapter.png'.format(_pre)})
                elif item['type'] == 'conferencePaper':
                    dct.update({'icon': 'icons/{}_conference.png'.format(_pre)})
                else:
                    dct.update({'icon': 'icons/{}_written.png'.format(_pre)})   
                xml_lst.append(dct)
        return xml_lst          


    def info_format(self, _item):
        """Format key information for item subtitle"""

        # Format creator string
        creator_list = []
        for item in _item['creators']:
            last = item['family']
            index = item['index']
            if item['type'] == 'editor':
                last = last + ' (ed.)'
            elif item['type'] == 'translator':
                last = last + ' (trans.)'
            creator_list.insert(index, last)
        
        if len(_item['creators']) == 0:
            creator_ref = 'xxx.'
        elif len(_item['creators']) == 1:
            creator_ref = ''.join(creator_list)
        elif len(_item['creators']) == 2:
            creator_ref = ' and '.join(creator_list)
        elif len(_item['creators']) > 2:
            creator_ref = ', '.join(creator_list[:-1])
            creator_ref = creator_ref + ', and ' + creator_list[-1]
        
        if not creator_ref[-1] in ['.', '!', '?']:
            creator_ref = creator_ref + '.'
        # Format date string
        try:
            date_final = _item['data']['date'] + '.'
        except KeyError:
            date_final = 'xxx.'
        # Format title string
        try:
            if not _item['data']['title'][-1] in ['.', '?', '!']:
                title_final = _item['data']['title'] + '.'
            else:
                title_final = _item['data']['title']
        except KeyError:
            title_final = "xxx."

        return [creator_ref, date_final, title_final]



###############################################################################
# Action Class                                                                #
###############################################################################

class ZotAction(object):
    """Actions Object"""

    def __init__(self, _input, _action,
                 data=None, settings=None, prefs=None):
        self.wf_obj = Workflow()
        self.input = _input
        self.action = _action

        if data == None:
            with open(self.wf_obj.datafile("zotero_db.json"), 'r') as file_obj:
                self.data = json.load(file_obj)
                file_obj.close()
        else: self.data = data

        if settings == None:
            with open(self.wf_obj.datafile("settings.json"), 'r') as file_obj:
                self.settings = json.load(file_obj)
                file_obj.close()
        else: self.settings = settings

        if prefs == None:
            with open(self.wf_obj.datafile("prefs.json"), 'r') as file_obj:
                self.prefs = json.load(file_obj)
                file_obj.close()
        else: self.prefs = prefs

        cache_files = ["temp_export.html", 
                       "temp_bibliography.txt", 
                       "temp_bibliography.html", 
                       "temp_attach_path.txt", 
                       "full_bibliography.html", 
                       "collection_query_result.txt", 
                       "tag_query_result.txt"]
        for file_ in cache_files:
            self.wf_obj.cachefile(file_) # Ensure all cache files exist

    ###########################################################################
    ### Primary API Method                                                  ###
    ###########################################################################

    def act(self):
        """Call proper method for action"""

        if self.action == 'cite':
            return self.export_citation()
        elif self.action == 'ref':
            return self.export_ref()
        elif self.action == 'cite_group':
            return self.export_group()
        elif self.action == 'append':
            return self.append_to_bib()
        elif self.action == 'save_coll':
            self.save_collection()
        elif self.action == 'save_tag':
            self.save_tag()
        elif self.action == 'att':
            self.open_attachment()
        elif self.action == 'bib':
            return self.read_save_bib()
        elif self.action == 'open':
            return self.open_item()

    ###########################################################################
    ### Export Methods                                                      ###
    ###########################################################################

    def export_citation(self):
        """Export full citation in MD or RTF format"""

        item_id = self.input.split('_')[1]
        if self.prefs['csl'] == "odt-scannable-cites":
            self._export_scannable_cite()
        else:
            zot = zotero.Zotero(self.settings['user_id'], 
                                self.settings['type'], 
                                self.settings['api_key'])
            ref = zot.item(item_id, content='bib', style=self.prefs['csl'])
            uref = unify(ref[0])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'citation')
                set_clipboard(citation.strip())
            elif self.prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'citation')
        return self.prefs['format']

    def export_ref(self):
        """Export short reference in MD or RTF format"""

        item_id = self.input.split('_')[1]
        if self.prefs['csl'] == 'odt-scannable-cites':
            self._export_scannable_cite()
        else:
            zot = zotero.Zotero(self.settings['user_id'], 
                                self.settings['type'], 
                                self.settings['api_key'])
            ref = zot.item(item_id, content='citation', style=self.prefs['csl'])
            uref = unify(ref[0][6:-7])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'ref')
                set_clipboard(citation.strip())
            elif self.prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'ref')
        return self.prefs['format']

    def export_group(self):
        """Export full bibliography in MD or RTF format"""

        [pre, item_id] = self.input.split(':')
        zot = zotero.Zotero(self.settings['user_id'], 
                            self.settings['type'], 
                            self.settings['api_key'])

        if pre == 'c':
            cites = zot.collection_items(item_id, 
                                        content='bib', 
                                        style=self.prefs['csl'])
        elif pre == 't':
            tag_name = self._get_tag_name(item_id)
            cites = zot.tag_items(tag_name, 
                                content='bib', 
                                style=self.prefs['csl'])

        if self.prefs['format'] == 'Markdown':
            md_cites = []
            for cite in cites:
                citation = self._export_markdown(cite, 'citation')
                md_cites.append(citation)

            sorted_md = sorted(md_cites)
            sorted_md.insert(0, 'WORKS CITED\n')
            set_clipboard('\n'.join(sorted_md))

        elif self.prefs['format'] == 'Rich Text':
            full_bib = self.wf_obj.cachefile("full_bibliography.html")

            bib_html = '<br>'.join([cite.encode('ascii', 'xmlcharrefreplace')
                                    for cite in cites])
            clean_html = self._clean_item(bib_html)
            html_cites = clean_html.split('<br>')
            sorted_html = sorted(html_cites)
            sorted_html.insert(0, 'WORKS CITED<br>')
            final_html = '<br>'.join(sorted_html)

            with open(full_bib, 'w') as file_obj:
                file_obj.write(final_html)
                file_obj.close()

            if html2rtf(full_bib):
                with open(full_bib, 'w') as file_obj:
                    file_obj.write('')
                    file_obj.close()
        return self.prefs['format']

    def append_to_bib(self):
        """Append full citation in MD or RTF format to temp bibliography"""

        item_id = self.input.split('_')[1]
        zot = zotero.Zotero(self.settings['user_id'], 
                            self.settings['type'], 
                            self.settings['api_key'])
        ref = zot.item(item_id, 
                       content='bib', 
                       style=self.prefs['csl'])
        uref = unify(ref[0])

        if self.prefs['format'] == 'Markdown':
            path = self.wf_obj.cachefile("temp_bibliography.txt")
            citation = self._export_markdown(uref, 'citation')
            with open(path, 'a') as file_obj:
                file_obj.write(citation.strip())
                file_obj.write('\n\n')
                file_obj.close()
        elif self.prefs['format'] == 'Rich Text':
            path = self.wf_obj.cachefile("temp_bibliography.html")
            with open(path, 'a') as file_obj:
                file_obj.write(uref[23:])
                file_obj.write('<br>')
                file_obj.close()
        return self.prefs['format']

    ###########################################################################
    ### Export helper functions                                             ###
    ###########################################################################

    def _export_markdown(self, html, style):
        """Convert to Markdown"""
        
        clean = self._clean_item(html)
        citation = html2text.html2text(clean)
        if style == 'citation':
            citation = re.sub("_(.*?)_", "*\\1*", citation)
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                citation = '[@' + citation.strip() + ']'
        return unify(citation)

    def _export_rtf(self, html, style):
        """Convert to RTF"""
        
        path = self.wf_obj.cachefile("temp_export.html")
        html = self._clean_item(html)
        if style == 'citation':
            html = html.encode('ascii', 'xmlcharrefreplace')[23:]
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                html = '[@' + html.strip() + ']'    
            html = html.encode('ascii', 'xmlcharrefreplace')

        with open(path, 'w') as file_:
            file_.write(html)
            file_.close()

        html2rtf(path) # Copy RTF to clipboard

    def _export_scannable_cite(self):
        """Convert to ODT Scannable Cite"""

        item_id = self.input.split('_')[1]
        uid = self.settings['user_id']
        set_clipboard(self._scan_cites(self.data, item_id, uid))
        return self.prefs['format']

    def _get_tag_name(self, key):
        """Get name of tag from `key`"""
        conn = sqlite3.connect(self.wf_obj.datafile("zotquery.sqlite"))
        cur = conn.cursor()
        sql_query = """SELECT name
            FROM tags
            WHERE key = "{}" """.format(key)
        tag_name = cur.execute(sql_query).fetchone()
        conn.close()
        return unify(tag_name[0])

    def _clean_item(self, item):
        """Clean up `item` formatting"""
        if self.prefs['csl'] != 'bibtex':
            item = re.sub(r"http(.*?)\.(?=<)", "", item)
            item = re.sub(r"doi(.*?)\.(?=<)", "", item)
        item = re.sub("’", "'", item)    
        item = re.sub("pp. ", "", item)
        return unify(item)


    def _scan_cites(self, zot_data, item_key, uid):
        """Exports ODT-RTF styled Scannable Cite"""

        for item in zot_data:
            if item['key'] == item_key:
                # Get YEAR var
                year = item['data']['date']
                # Get and format CREATOR var
                if len(item['creators']) == 1:
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
        prefix = ''
        suffix = ''
        info = last + ', ' + year
        data = 'zu:' + uid + ':' + item_key
        scannable_str = ' | '.join([prefix, info, '', suffix, data])

        scannable_cite = '{' + scannable_str + '}'
        return unify(scannable_cite)

    ############################################################################
    ### Save sub-methods                                                     ###
    ############################################################################

    def save_collection(self):
        """Save collection info to cache"""

        path = self.wf_obj.cachefile("collection_query_result.txt")
        with open(path, 'w') as file_obj:
            file_obj.write(self.input.encode('utf-8'))
            file_obj.close()

    def save_tag(self):
        """Save tag info to cache"""

        path = self.wf_obj.cachefile("tag_query_result.txt")
        with open(path, 'w') as file_obj:
            file_obj.write(self.input.encode('utf-8'))
            file_obj.close()

    def read_save_bib(self):
        """Read saved biblio from cache"""
        if self.prefs['format'] == 'Markdown':
            txt_path = self.wf_obj.cachefile("temp_bibliography.txt")
            with open(txt_path, 'r') as file_obj:
                bib = file_obj.read()
                file_obj.close()
            sorted_l = sorted(bib.split('\n\n'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED'
            else:
                sorted_l.insert(0, 'WORKS CITED')
            set_clipboard('\n\n'.join(sorted_l))

            with open(txt_path, 'w') as file_obj:
                file_obj.write('')
                file_obj.close()
            return self.prefs['format']

        elif self.prefs['format'] == 'Rich Text':
            html_path = self.wf_obj.cachefile("temp_bibliography.html")
            with open(html_path, 'r') as file_obj:
                bib = file_obj.read()
                file_obj.close()
            sorted_l = sorted(bib.split('<br>'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED<br>'
            else:
                sorted_l.insert(0, 'WORKS CITED<br>')
            html_string = '<br><br>'.join(sorted_l)
            # Write html to temporary bib file
            with open(html_path, 'w') as file_obj:
                file_obj.write(html_string)
                file_obj.close()
            # Convert html to RTF and copy to clipboard
            if html2rtf(html_path):
                # Write blank file to bib file
                with open(html_path, 'w') as file_:
                    file_.write('')
                    file_.close()
                return self.prefs['format']


    ####################################################################
    # Open sub-methods
    ####################################################################

    def open_item(self):
        """Open item in Zotero client"""

        if self.prefs['client'] == "Standalone":
            app_id = "org.zotero.zotero"
        elif self.prefs['client'] == "Firefox":
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
            """.format(self.input, app_id)
        return run_applescript(scpt_str)

    def open_attachment(self):
        """Open item's attachment in default app"""
        if os.path.isfile(self.input):
            subprocess.Popen(['open', self.input], stdout=subprocess.PIPE)
        # if self.input is item key
        else:
            # Get the item's attachement path and attachment key
            item_id = self.input.split('_')[1]
            for item in self.data:
                if item_id == item['key']:
                    for jtem in item['attachments']:
                        if os.path.isfile(jtem['path']):
                            subprocess.Popen(['open', jtem['path']],
                                             stdout=subprocess.PIPE)



###############################################################################
# Main Function                                                               #
###############################################################################

def main(wf_obj):
    """Accept Alfred's args and pipe to proper Class"""

    argv = wf_obj.args
    #argv = ['--config', 'prefs']

    if argv[0] == '--cache':
        _force = boolify(argv[1]) # True
        _personal_only = boolify(argv[2]) # False
        z_cacher = ZotCache(_force, _personal_only)
        print z_cacher.cache()
    
    elif argv[0] == '--config':
        _method = argv[1] # 'prefs'
        z_configurator = ZotConfig(_method)
        print z_configurator.config()
    
    elif argv[0] == '--filter':
        _query = argv[1] # "oeuvre inconnue"
        _scope = argv[2] # "titles"
        try:
            personal_only = boolify(argv[3])
        except IndexError:
            personal_only = False
        z_filter = ZotFilter(_query, _scope, personal_only)
        z_filter.filter()
    
    elif argv[0] == '--action':
        _key = argv[1] # '266264_JGI5I4TE'
        _action = argv[2] # 'open'
        z_actor = ZotAction(_key, _action)
        print z_actor.act()
    

if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
