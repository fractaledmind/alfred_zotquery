#!/usr/bin/python
# encoding: utf-8

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
            'in-collection' = search within saved collection using `general` scope
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dependencies'))
import html2md
import zq_utils as z
from pyzotero import zotero
from workflow import Workflow


################################################################################
################################################################################
##########     Cache Object                                           ##########
################################################################################
################################################################################

class ZotCache(object):

    def __init__(self, force, personal_only):
        """Initialize the cache object"""

        self.force = force
        self.personal_only = personal_only
        self.wf = Workflow()

        self.zot_db = self.get_path('database_path')
        self.json_db = self.wf.datafile("zotero_db.json")
        self.clone_db = self.wf.datafile("zotquery.sqlite")
        self.backup_db = self.wf.datafile("old_db.json")

        self.conn = sqlite3.connect(self.clone_db)
        self.attachment_exts = [".pdf", "epub"]


    ################################################################################
    ### Setup Functions                                                          ###
    ################################################################################

    def setup(self):
        """Ensure configuration and create copies"""

        if os.path.exists(self.wf.datafile("first-run.txt")):
            # Back-up old Cache
            if os.path.exists(self.json_db):
                shutil.copyfile(self.json_db, 
                                self.backup_db)

            # Begin new cache?
            if self.force or z.check_cache()[0]:     
                shutil.copyfile(self.zot_db, self.clone_db)
                return True
            else:
                return False

        # Not configured
        else:
            script = 'tell application "Alfred 2" to search "z:config"'
            subprocess.call(['osascript', '-e', script])
            return False


    def get_path(self, _type): 
        """Read paths.json file from non-volatile storage"""

        with open(self.wf.datafile("paths.json"), 'r') as f:
            _paths = json.load(f)
            f.close()
        return z.to_unicode(_paths[_type])


    ################################################################################
    ### SQLite Functions                                                         ###
    ################################################################################

    def sqlite_get(self, _sql):
        """Retrieve data from Zotero sqlite database"""
        
        cur = self.conn.cursor() 
        _info = cur.execute(_sql)
        return _info


    def sqlite_close(self):
        """Close connection to database"""
        self.conn.close() 


    ################################################################################
    ### SQLite Methods                                                         ###
    ################################################################################


    def info_query(self):
        """Retrieve (key, id, type id) from item"""

        info_sql = """SELECT key, itemID, itemTypeID, libraryID
            FROM items
            WHERE 
                itemTypeID != 14 
                and itemTypeID != 1
            ORDER BY dateAdded DESC"""
        return self.sqlite_get(info_sql)


    def creator_info_query(self, creator_data_id, creator_type_id):
        """Retrieve (last name, first name, type) from item"""

        creator_info_sql = """SELECT creatorData.lastName, creatorData.firstName, creatorTypes.creatorType 
            FROM creatorData, creatorTypes
            WHERE
                creatorDataID = {0}
                and creatorTypeID = {1}""".format(creator_data_id, creator_type_id)
        return self.sqlite_get(creator_info_sql)


    def attachment_info_query(self, item_id):
        """Retrieve (tag id) from item"""

        attachment_info_sql = """SELECT path, itemID
            FROM itemAttachments
            WHERE sourceItemID = {0}""".format(item_id)
        return self.sqlite_get(attachment_info_sql)


    def collection_info_query(self, collection_id):
        """Retrieve (collection name, collection key) from item"""

        collection_info_sql = """SELECT collectionName, key
            FROM collections
            WHERE 
                collectionID = {0}
                and libraryID is null""".format(collection_id)
        return self.sqlite_get(collection_info_sql)


    def group_info_query(self, collection_id):
        """Retrieve (collection name, collection key, group name, group id) from item"""

        group_info_sql = """SELECT collections.collectionName, collections.key, groups.name, groups.libraryID
            FROM collections, groups
            WHERE 
                collections.collectionID = {0}
                and collections.libraryID is not null""".format(collection_id)
        return self.sqlite_get(group_info_sql)  


    def tag_info_query(self, tag_id):
        """Retrieve (tag name, tag key) from item"""

        tag_info_sql = """SELECT name, key
                FROM tags
                WHERE tagID = {0}""".format(tag_id)
        return self.sqlite_get(tag_info_sql)


    def note_info_query(self, item_id):
        """Retrieve (note) from item"""

        note_info_sql = """SELECT note
            FROM itemNotes
            WHERE sourceItemID = {0}""".format(item_id)
        return self.sqlite_get(note_info_sql)


    def type_query(self, type_id):
        """Retrieve (type name) from item"""

        type_sql = """SELECT typeName
            FROM itemTypes
            WHERE itemTypeID = {0}""".format(type_id)
        return self.sqlite_get(type_sql)


    def creators_query(self, item_id):
        """Retrieve (creator id, creator type id, order index) from item"""

        creators_sql = """SELECT creatorID, creatorTypeID, orderIndex
            FROM itemCreators
            WHERE itemID = {0}""".format(item_id)
        return self.sqlite_get(creators_sql)


    def creator_id_query(self, creator_id):
        """Retrieve (creator data id) from item"""

        creator_id_sql = """SELECT creatorDataID
            FROM creators
            WHERE creatorID = {0}""".format(creator_id)
        return self.sqlite_get(creator_id_sql)


    def metadata_id_query(self, item_id):
        """Retrieve (field id, value id) from item"""

        metadata_id_sql = """SELECT fieldID, valueID
            FROM itemData
            WHERE itemID = {0}""".format(item_id)
        return self.sqlite_get(metadata_id_sql)


    def field_name_query(self, field_id):
        """Retrieve (field name) from item"""

        field_name_sql = """SELECT fieldName
            FROM fields
            WHERE fieldID = {0}""".format(field_id)
        return self.sqlite_get(field_name_sql)


    def value_name_query(self, value_id):
        """Retrieve (value name) from item"""

        value_name_sql = """SELECT value
            FROM itemDataValues
            WHERE valueID = {0}""".format(value_id)
        return self.sqlite_get(value_name_sql)


    def collection_id_query(self, item_id):
        """Retrieve (collection id) from item"""

        collection_id_sql = """SELECT collectionID
            FROM collectionItems
            WHERE itemID = {0}""".format(item_id)
        return self.sqlite_get(collection_id_sql)


    def tag_id_query(self, item_id):
        """Retrieve (tag id) from item"""

        tag_id_sql = """SELECT tagID
            FROM itemTags
            WHERE itemID = {0}""".format(item_id)
        return self.sqlite_get(tag_id_sql)


    def attachment_key_query(self, attachment_id):
        """Retrieve (attachment key) from item"""

        attachment_key_sql = """SELECT items.key
            FROM items
            WHERE itemID = {0}""".format(attachment_id)
        return self.sqlite_get(attachment_key_sql)


    ################################################################################
    ### Cache Methods                                                            ###
    ################################################################################

    def cache(self):

        if self.setup():
            json_cache = self.get_cache()

            with open(self.wf.datafile("zotero_db.json"), 'w') as f:
                f.write(json_cache.encode('utf-8'))
                f.close()


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
            (item_key, item_id, item_type_id, library_id) = basic
            item_dict['key'] = item_key
            if library_id == None: library_id = '0'
            item_dict['library'] = unicode(library_id)

            type_name = ''
            (type_name,) = self.type_query(item_type_id).fetchone()
            item_dict['type'] = type_name

            ##### Creators Info
            item_dict['creators'] = []
            creators_data = self.creators_query(item_id)
            for _creator in creators_data:
                creator_id = creator_type_id = creator_id = order_index = ''
                (creator_id, creator_type_id, order_index) = _creator
                (creator_data_id,) = self.creator_id_query(creator_id).fetchone()
                creators_info = self.creator_info_query(creator_data_id, creator_type_id)
                for creator_info in creators_info:
                    first_name = last_name = ''
                    (last_name, first_name, c_type) = creator_info
                    item_dict['creators'].append({'family': last_name, 
                                                'given': first_name, 
                                                'type': c_type, 
                                                'index': order_index})

            ##### Meta-Data Info
            items_data = self.metadata_id_query(item_id)
            for _item in items_data:
                field_id = value_id = value_name = ''
                (field_id, value_id) = _item
                (field_name,) = self.field_name_query(field_id).fetchone()
                if field_name not in item_meta:
                    item_meta[field_name] = ''
                    (value_name,) = self.value_name_query(value_id).fetchone()
                    try:
                        if field_name == 'date':
                            item_meta[field_name] = str(value_name[0:4])
                        else:
                            item_meta[field_name] = str(value_name)
                    except:
                        item_meta[field_name] = unicode(value_name)
            item_dict['data'] = item_meta

            ##### Collection Info
            item_dict['zot-collections'] = []
            collections_data = self.collection_id_query(item_id)
            for _collection in collections_data:
                collection_id = ''
                (collection_id,) = _collection
                collection_info = self.collection_info_query(collection_id).fetchall()
                if collection_info != []:
                    (collection_name, collection_key) = collection_info[0]
                    item_dict['zot-collections'].append({'name': collection_name,
                                                    'key': collection_key,
                                                    'library_id': '0',
                                                    'group': 'personal'})
                else:
                    if self.personal_only == False:
                        (collection_name, collection_key, group_name, library_id) = self.group_info_query(collection_id).fetchone()
                        item_dict['zot-collections'].append({'name': collection_name,
                                                        'key': collection_key,
                                                        'library_id': str(library_id),
                                                        'group': group_name})

            ##### Tag Info
            item_dict['zot-tags'] = []
            tags_data = self.tag_id_query(item_id)
            for _tag in tags_data:
                tag_id = ''
                (tag_id,) = _tag
                (tag_name, tag_key) = self.tag_info_query(tag_id).fetchone()
                item_dict['zot-tags'].append({'name': tag_name,
                                            'key': tag_key})

            ##### Attachment Info
            item_dict['attachments'] = []
            attachments_data = self.attachment_info_query(item_id)
            for _attachment in attachments_data:
                if _attachment[0] != None:
                    (attachment_path, attachment_id) = _attachment
                    if attachment_path[:8] == "storage:":
                        attachment_path = attachment_path[8:]
                        if attachment_path[-4:].lower() in self.attachment_exts:
                            (attachment_key,) = self.attachment_key_query(attachment_id).fetchone()
                            storage_path = z.get_path('storage_path')
                            base_path = os.path.join(storage_path, attachment_key)
                            final_path = os.path.join(base_path, attachment_path)
                            item_dict['attachments'].append({'name': attachment_path,
                                                        'key': attachment_key,
                                                        'path': final_path})
                    elif attachment_path[:12] == "attachments:":
                        attachment_path = attachment_path[12:]
                        if attachment_path[-4:].lower() in self.attachment_exts:
                            (attachment_key,) = self.attachment_key_query(attachment_id).fetchone()
                            base = z.get_path('link-attachments_path')
                            final_path = os.path.join(base, attachment_path)
                            item_dict['attachments'].append({'name': attachment_path,
                                                        'key': attachment_key,
                                                        'path': final_path})
                    else:
                        attachment_name = attachment_path.split('/')[-1]
                        item_dict['attachments'].append({'name': attachment_name,
                                                    'key': None,
                                                    'path': attachment_path})

            ##### Notes Info
            item_dict['notes'] = []
            notes_data = self.note_info_query(item_id)
            for _note in notes_data:
                note = ''
                (note,) = _note
                item_dict['notes'].append(note[33:-10])

            ##### Add item dict to running list
            _items.append(item_dict)

        final_json = json.dumps(_items, sort_keys=False, indent=4, separators=(',', ': '))
        self.sqlite_close()

        return final_json


################################################################################
################################################################################
##########   Config Class                                             ##########
################################################################################
################################################################################


class ZotConfig(object):

    def __init__(self, scope):
        self.zot_api = wf.workflowfile('dependencies/config_zotero-api.scpt')
        self.set_prefs = wf.workflowfile('dependencies/config_export-prefs.scpt')

        self.scope = scope


    def config(self):

        if self.scope == 'api':
            self.set_api_data()

        elif self.scope == 'prefs':
            self.set_export_prefs()

        elif self.scope == 'paths':
            self.set_zot_paths()


    
    def set_api_data(self):
        """Save Zotero API info to `settings.json` file"""

        return subprocess.call(['osascript', self.zot_api])


    def set_export_prefs(self):
        """Save export prefs to `prefs.json` file"""

        subprocess.call(['osascript', self.set_prefs])


    def set_zot_paths(self):
        """Save paths to key Zotero items to `paths.json` file"""

        # Check to see if already configured
        if not os.path.exists(wf.datafile("paths.json")):

            # Path to apps
            _zs = os.environ["HOME"] + '/Library/Application Support/Zotero/'
            _zf = os.environ["HOME"] + '/Library/Application Support/Firefox/'

            # Profile paths
            zs_path = z.get_profile(_zs)
            zf_path = z.get_profile(_zf)

            # Path to preferences files
            zs_pref_path = zs_path + '/prefs.js'
            zf_pref_path = zf_path + '/prefs.js'

            
            # If only Firefox extension
            if os.path.exists(zf_pref_path):
                # Try to get data dir and linked attachments from Firefox prefs
                data_path = self._get_paths(zf_pref_path)[0]
                attach_path = self._get_paths(zf_pref_path)[1]
                default_path = zf_path

                if data_path == None:
                    if os.path.exists(zs_pref_path):
                        # Try to get data directory from ZS prefs
                        data_path = self._get_paths(zs_pref_path)[0]
                        default_path = zs_path
                elif attach_path == None:
                    if os.path.exists(zs_pref_path):
                        # Try to get linked attachments directory from ZS prefs
                        attach_path = self._get_paths(zs_pref_path)[1]
                        default_path = zs_path
                
            elif os.path.exists(zs_pref_path):
                data_path = self._get_paths(zs_pref_path)[0]
                attach_path = self._get_paths(zs_pref_path)[1]
                default_path = zs_path

            # Try paths to storage directory and zotero.sqlite file
            storage_path = os.path.join(data_path, 'storage')
            db_path = os.path.join(data_path, 'zotero.sqlite')

            # Check if prefs paths exist
            if os.path.exists(storage_path):
                pass
            else:
                # If not, have user select
                a_script = """
                    set ui to load script POSIX file (POSIX path of "{0}")
                    set choice to ui's choose_folder({{z_prompt:"Select Zotero storage folder.", z_def:"{1}"}})
                """.format(wf.workflowfile('dependencies/_ui-helpers.scpt'), default_path)
                #storage_path = applescript.asrun(a_script)[0:-1]
                storage_path = subprocess.call(['osascript', '-e', a_script])

            if os.path.exists(db_path):
                pass
            else:
                a_script = """
                    set ui to load script POSIX file (POSIX path of "{0}")
                    set choice to ui's choose_file({{z_prompt:"Select Zotero sqlite database.", z_def:"{1}"}})
                """.format(wf.workflowfile('dependencies/_ui-helpers.scpt'), default_path)
                #db_path = applescript.asrun(a_script)[0:-1]
                db_path = subprocess.call(['osascript', '-e', a_script])

            if os.path.exists(attach_path): 
                pass
            else:
                a_script = """
                    set ui to load script POSIX file (POSIX path of "{0}")
                    set choice to ui's choose_folder({{z_prompt:"Select Zotero folder where linked attachments reside.", z_def:POSIX path of (path to documents folder)}})
                """.format(wf.workflowfile('dependencies/_ui-helpers.scpt'))
                #attach_path = applescript.asrun(a_script)[0:-1]
                attach_path = subprocess.call(['osascript', '-e', a_script])

            # Store the paths in non-volatile storage
            with open(wf.datafile("paths.json"), 'w') as f:
                _dict = {'storage_path': storage_path, 
                        'database_path': db_path, 
                        'link-attachments_path': attach_path}
                _json = json.dumps(_dict, 
                                    sort_keys=False, 
                                    indent=4, 
                                    separators=(',', ': '))
                f.write(_json.encode('utf-8'))
                f.close()
                return "Zotero paths saved!"
        else:
            return "Zotero paths alread saved."


    def _get_paths(self, prefs):
        """Search prefs.js file for Firefox or Standalone for all data"""

        # Regexs
        last_data_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.lastDataDir\",\s\"(.*?)\"\);")
        data_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.dataDir\",\s\"(.*?)\"\);")
        base_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.baseAttachmentPath\",\s\"(.*?)\"\);")

        with open(prefs, 'r') as f:
            _prefs = f.read()
            f.close()
        # Get path to data directory
        data_dir = re.search(last_data_dir_re, _prefs)
        try:
            data_path = data_dir.group(1)
        except:
            try:
                data_dir = re.search(data_dir_re, _prefs)
                data_path = data_dir.group(1)
            except:
                data_path = None

        # Get path to directory for linked attachments
        attach_dir = re.search(base_dir_re, _prefs)
        try:    
            attach_path = attach_dir.group(1)
        except:
            attach_path = None
        return [data_path, attach_path]



################################################################################
################################################################################
##########   Filter Class                                             ##########
################################################################################
################################################################################


class ZotFilter(object):
    
    def __init__(self, query, scope, data=[], test_group=None, personal_only=False):
        self.wf = Workflow()
        self.queries = query.split()
        self.scope = scope

        if self.first_run_test() and self.query_len_test(): 
            pass
            
        if data == []:
            with open(self.wf.datafile("zotero_db.json"), 'r') as f:
                self.data = json.load(f)
                f.close()
            if personal_only == True:
                personal_data = []
                ids = []
                for i in self.data:
                    if i['zot-collections'] != []:
                        for c in i['zot-collections']:
                            if c['group'] == 'personal':
                                if not i['id'] in ids:
                                    personal_data.append(i)
                                    ids.append(i['id'])
                self.data = personal_data
        else:
            self.data = data

        self.test_group = test_group

    
    ####################################################################
    # API method
    ####################################################################

    def filter(self):
        """Main API method"""

        if self.scope in ['general', 'creators', 'titles', 'notes']:
            self.filters_simple()

        elif self.scope in ['collections', 'tags']:
            self.filters_groups()

        elif self.scope in ['in-collection', 'in-tag']:
            self.filters_in_groups()

        elif self.scope == 'attachments':
            self.filters_atts()

        elif self.scope == 'debug':
            self.filters_debug()

        elif self.scope == 'new':
            return self.filters_new()

    ####################################################################
    # Sub-Methods
    ####################################################################

    def filters_simple(self):
        """Simple Filter method"""
        
        data = self.data
        for query in self.queries:
            data = self.wf.filter(query, data, key=lambda x: z.zot_string(x, self.scope))
        
        if data != []:
            # Format matched items for display
            prep_res = z.prepare_feedback(data)  
            for item in prep_res:
                self.wf.add_item(**item)
            self.wf.send_feedback()
        else:
            self.no_results()

    def filters_groups(self):
        """Group Filter method"""
        
        data = self._get_group_data(self.test_group)
        if data != []:
            for query in self.queries:
                data = self.wf.filter(query, data, key=lambda x: x[0])
            
            if data != []:
                if self.scope == "collections":
                    _pre = "c:"
                elif self.scope == "tags":
                    _pre = "t:"
                for item in data:
                    self.wf.add_item(item[0], self._sub, 
                        arg=_pre + item[1], 
                        valid=True, 
                        icon=self._icon)
                self.wf.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filters_in_groups(self):
        """In-Group Filter method"""

        data = self._get_ingroup_data()
        if data != []:
            for query in self.queries:
                data = self.wf.filter(query, data, key=lambda x: z.zot_string(x))
            
            if data != []:
                prep_res = z.prepare_feedback(data)  
                for item in prep_res:
                    self.wf.add_item(**item)
                self.wf.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filters_atts(self):
        """Attachments Filter method"""

        data = self._get_atts_data()
        if data != []:
            for query in self.queries:
                data = self.wf.filter(query, data, key=lambda x: z.zot_string(x))
            
            if data != []:
                for item in data:
                    info = z.info_format(item)
                    title = item['data']['title']
                    sub = info[0] + ' ' + info[1]
                    self.wf.add_item(title, sub, 
                        arg=item['attachments'][0]['path'], 
                        valid=True,
                        type='file',
                        icon='icons/n_pdf.png')
                self.wf.send_feedback()
            else:
                self.no_results()
        else:
            self.no_results()

    def filters_debug(self):
        """Debug options Filter method"""

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
        self.wf.send_feedback()

    def filters_new(self):
        """New items Filter method"""

        curr_ids = [item['id'] for item in self.data]
        # Get previous Zotero data from JSON cache
        with open(self.wf.datafile('old_db.json'), 'r') as f:
            old_data = json.load(f)
            f.close()
        old_ids = [item['id'] for item in old_data]
        # Get list of newly added items
        new_ids = list(set(curr_ids) - set(old_ids))
        new_items = []
        for i in new_ids:
            new_items += [item for item in self.data if item['id'] == i]
        #return new_items
        res = z.prepare_feedback(new_items)
        if res != []:
            for a in res:
                self.wf.add_item(**a)
            self.wf.send_feedback()
        else:
            self.no_results()

    ####################################################################
    # Get sub-sets of data methods
    ####################################################################

    def _get_group_data(self, test_group):
        """Sub-Method for Group data"""

        if test_group == None:
            conn = sqlite3.connect(self.wf.datafile("zotquery.sqlite"))
            cur = conn.cursor()
            
            if self.scope == "collections":
                sql_query = """
                    select collections.collectionName, collections.key
                    from collections
                """
                self._sub = "Collection"
                self._icon = "icons/n_collection.png"
            elif self.scope == "tags":
                sql_query = """
                    select tags.name, tags.name
                    from tags
                """
                self._sub = "Tag"
                self._icon = "icons/n_tag.png"

            group_data = cur.execute(sql_query).fetchall()
            conn.close()
        else:
            group_data = test_group
            self._sub = "Test"
            self._icon = "icon.png"
        return group_data   

    def _get_ingroup_data(self, test_group=None):
        """Sub-Method for In-Group data"""

        term = self.scope.split('-')[1]
        if test_group == None:
            with open(self.wf.cachefile("{0}_query_result.txt").format(term), 'r') as f:
                _inp = f.read().decode('utf-8')
                f.close()
        else:
            _inp = test_group
        
        _items = []
        for item in self.data:
            for jtem in item['zot-{0}s'.format(term)]:
                if _inp == jtem['key']: 
                    _items.append(item)
        return _items
    
    def _get_atts_data(self):
        """Sub-Method for Attachments data"""

        _items = []
        for item in self.data:
            if item['attachments'] != []:
                _items.append(item)
        return _items


    ####################################################################
    # Helper functions
    ####################################################################

    def first_run_test(self):
        """Check if workflow is configured"""

        if not os.path.exists(self.wf.datafile("first-run.txt")):
            script = 'tell application "Alfred 2" to search "z:config"'
            subprocess.call(['osascript', '-e', script])
        else: return True

    def query_len_test(self):
        """Check if query terms have enough letters"""

        for query in self.queries:
            if len(query) <= 2:
                self.wf.add_item("Error!", "Need at least 3 letters to execute search", 
                    icon="icons/n_delay.png")
                self.wf.send_feedback()
                sys.exit(0)
            else: return True

    def no_results(self):
        """Return no results"""

        self.wf.add_item("Error!", "No results found.", 
                        icon="icons/n_error.png")
        self.wf.send_feedback()



################################################################################
################################################################################
########## Action Class                                               ##########
################################################################################
################################################################################

class ZotAction(object):
    
    def __init__(self, _input, _action, data=[], settings=[], prefs=[]):
        self.wf = Workflow()
        self.input = _input
        self.action = _action

        if data == []:
            with open(self.wf.datafile("zotero_db.json"), 'r') as f:
                self.data = json.load(f)
                f.close()
        else: self.data = data

        if settings == []:
            with open(self.wf.datafile("settings.json"), 'r') as f:
                self.settings = json.load(f)
                f.close()
        else: self.settings = settings

        if prefs == []:
            with open(self.wf.datafile("prefs.json"), 'r') as f:
                self.prefs = json.load(f)
                f.close()
        else: self.prefs = prefs

        cache_files = ["temp_export.html", "temp_bibliography.txt", "temp_bibliography.html", "temp_attach_path.txt", "full_bibliography.html", "collection_query_result.txt", "tag_query_result.txt"]
        for _file in cache_files:
            self.wf.cachefile(_file)


    def act(self):
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


    ####################################################################
    # Export API methods
    ####################################################################

    def export_citation(self):
        item_id = self.input.split('_')[1]

        if self.prefs['csl'] == "odt-scannable-cites":
            self._export_scannable_cite()

        else:

            zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
            ref = zot.item(item_id, content='bib', style=self.prefs['csl'])
            uref = z.to_unicode(ref[0])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'citation')
                z.set_clipboard(citation.strip())

            elif self.prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'citation')
        return self.prefs['format']


    def export_ref(self):
        item_id = self.input.split('_')[1]

        if self.prefs['csl'] == 'odt-scannable-cites':
            self._export_scannable_cite()

        else:

            zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
            ref = zot.item(item_id, content='citation', style=self.prefs['csl'])
            uref = z.to_unicode(ref[0][6:-7])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'ref')
                z.set_clipboard(citation.strip())
                
            elif self.prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'ref')
        return self.prefs['format']

    
    def export_group(self):

        _inp = self.input.split(':')
        zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])

        if _inp[0] == 'c':
            cites = zot.collection_items(_inp[1], content='bib', style=self.prefs['csl'])
        elif _inp[0] == 't':
            cites = zot.tag_items(_inp[1], content='bib', style=self.prefs['csl'])

        if self.prefs['format'] == 'Markdown':

            md_cites = []
            for ref in cites:
                citation = html2md.html2text(ref)
                if self.prefs['csl'] != 'bibtex':
                    citation = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
                    citation = re.sub("_(.*?)_", "*\\1*", citation)
                md_cites.append(citation)

            sorted_md = sorted(md_cites)
            sorted_md.insert(0, 'WORKS CITED\n')
            z.set_clipboard('\n'.join(sorted_md))

        elif self.prefs['format'] == 'Rich Text':

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                for ref in cites:
                    f.write(ref.encode('ascii', 'xmlcharrefreplace'))
                    f.write('<br>')
                f.close()

            with open(self.wf.cachefile("full_bibliography.html"), 'r') as f:
                bib_html = f.read()
                f.close()
            
            if self.prefs['csl'] != 'bibtex':
                bib_html = re.sub(r"http(.*?)\.(?=<)", "", bib_html)
                bib_html = re.sub(r"doi(.*?)\.(?=<)", "", bib_html)
            bib_html = re.sub("pp. ", "", bib_html)
            
            html_cites = bib_html.split('<br>')
            sorted_html = sorted(html_cites)
            sorted_html.insert(0, 'WORKS CITED<br>')
            final_html = '<br>'.join(sorted_html)

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                f.write(final_html)
                f.close()

            a_script = """
                do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
                """.format(self.wf.cachefile("full_bibliography.html"))
            #applescript.asrun(a_script)
            subprocess.call(['osascript', '-e', a_script])

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                f.write('')
                f.close()
        return self.prefs['format']


    def append_to_bib(self):

        item_id = self.input.split('_')[1]

        zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
        ref = zot.item(item_id, content='bib', style=self.prefs['csl'])
        uref = z.to_unicode(ref[0])

        if self.prefs['format'] == 'Markdown':
            citation = self._export_markdown(uref, 'citation')
            with open(self.wf.cachefile("temp_bibliography.txt"), 'a') as f:
                f.write(citation.strip())
                f.write('\n\n')
                f.close()

        elif self.prefs['format'] == 'Rich Text':
            with open(self.wf.cachefile("temp_bibliography.html"), 'a') as f:
                f.write(uref[23:])
                f.write('<br>')
                f.close()
        return self.prefs['format']

    ####################################################################
    # Export helper functions
    ####################################################################

    def _export_markdown(self, html, style):
        
        if self.prefs['csl'] != 'bibtex':
            html = re.sub("(?:http)(.*?)$|pp. ", "", html)
        
        citation = html2md.html2text(html)
        if style == 'citation':
            citation = re.sub("_(.*?)_", "*\\1*", citation)
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                citation = '[@' + citation.strip() + ']'
        return citation

    def _export_rtf(self, html, style):

        if self.prefs['csl'] != 'bibtex':
            html = re.sub("(?:http)(.*?)$|pp. ", "", html)

        if style == 'citation':
            html = html.encode('ascii', 'xmlcharrefreplace')[23:]
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                html = '[@' + html.strip() + ']'    
            html = html.encode('ascii', 'xmlcharrefreplace')

        with open(self.wf.cachefile("temp_export.html"), 'w') as f:
            f.write(html)
            f.close()
        a_script = """
            do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
            """.format(self.wf.cachefile("temp_export.html"))
        #applescript.asrun(a_script)
        subprocess.call(['osascript', '-e', a_script])


    def _export_scannable_cite(self):
        item_id = self.input.split('_')[1]
        uid = self.settings['user_id']
        z.set_clipboard(z.scan_cites(self.data, item_id, uid))
        return self.prefs['format']


    ####################################################################
    # Save API methods
    ####################################################################

    def save_collection(self):
        with open(self.wf.cachefile("collection_query_result.txt"), 'w') as f:
            f.write(self.input.encode('utf-8'))
            f.close()

    def save_tag(self):
        with open(self.wf.cachefile("tag_query_result.txt"), 'w') as f:
            f.write(self.input.encode('utf-8'))
            f.close()

    def read_save_bib(self):
        if self.prefs['format'] == 'Markdown':
            with open(self.wf.cachefile("temp_bibliography.txt"), 'r') as f:
                bib = f.read()
                f.close()
            sorted_l = sorted(bib.split('\n\n'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED'
            else:
                sorted_l.insert(0, 'WORKS CITED')
            z.set_clipboard('\n\n'.join(sorted_l))

            with open(self.wf.cachefile("temp_bibliography.txt"), 'w') as f:
                f.write('')
                f.close()
            return self.prefs['format']

        elif self.prefs['format'] == 'Rich Text':
            with open(self.wf.cachefile("temp_bibliography.html"), 'r') as f:
                bib = f.read()
                f.close()
            sorted_l = sorted(bib.split('<br>'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED<br>'
            else:
                sorted_l.insert(0, 'WORKS CITED<br>')
            html_string = '<br><br>'.join(sorted_l)
            # Write html to temporary bib file
            with open(self.wf.cachefile("temp_bibliography.html"), 'w') as f:
                f.write(html_string)
                f.close()
            # Convert html to RTF and copy to clipboard
            a_script = """
                do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
                """.format(self.wf.cachefile("temp_bibliography.html"))
            #applescript.asrun(a_script)
            subprocess.call(['osascript', '-e', a_script])

            # Write blank file to bib file
            with open(self.wf.cachefile("temp_bibliography.html"), 'w') as f:
                f.write('')
                f.close()
            return self.prefs['format']


    ####################################################################
    # Attachment API method
    ####################################################################

    def open_item(self):
        """Open item in Zotero"""

        client = self.prefs['client']

        if client == "Standalone":
            a_script = """
                if application id "org.zotero.zotero" is not running then
                    tell application id "org.zotero.zotero"
                        launch
                        activate
                        delay 1
                        open location "zotero://select/items/" & "{0}"
                    end tell
                else
                    tell application id "org.zotero.zotero"
                        activate
                        open location "zotero://select/items/" & "{0}"
                    end tell
                end if
            """
        elif client == "Firefox":
            a_script = """   
                if application id "org.mozilla.firefox" is not running then
                    tell application id "org.mozilla.firefox"
                        launch
                        activate
                        delay 1
                        open location "zotero://select/items/" & "{0}"                 
                        delay 1
                        open location "zotero://select/items/" & "{0}"             
                    end tell
                else
                    tell application id "org.mozilla.firefox"
                        activate
                        delay 0.5
                        open location "zotero://select/items/" & "{0}"             
                    end tell
                end if
            """.format(self.input)
        return subprocess.call(['osascript', '-e', a_script])


    def open_attachment(self):

        if os.path.isfile(self.input):
            subprocess.Popen(['open', self.input], shell=False, stdout=subprocess.PIPE)
        # if self.input is item key
        else:
            # Get the item's attachement path and attachment key
            item_id = self.input.split('_')[1]
            for item in self.data:
                if item_id == item['key']:
                    for jtem in item['attachments']:
                        path = jtem['path']
                        key = jtem['key']

                        if os.path.isfile(path):
                            subprocess.Popen(['open', path], shell=False, 
                                            stdout=subprocess.PIPE)
                        else:
                            # Open the attachment in Zotero
                            a_script = """
                            if application id "org.zotero.zotero" is not running then
                                tell application id "org.zotero.zotero" to launch
                            end if
                            delay 0.5
                            tell application id "org.zotero.zotero"
                                activate
                                delay 0.3
                                open location "zotero://select/items/0_{0}"
                            end tell
                            """.format(key)
                            subprocess.call(['osascript', '-e', a_script])


################################################################################
################################################################################
##########     Main Function                                          ##########
################################################################################
################################################################################

def main(wf):
    """Accept Alfred's args and pipe to proper Class"""

    argv = wf.args

    if argv[0] == '--cache':
        _force = argv[1] # True
        _personal_only = argv[2] # False
        zc = ZotCache(_force, _personal_only)
        zc.cache()
    
    elif argv[0] == '--config':
        _method = argv[1] # 'api'
        zc = ZotConfig(_method)
        zc.config()
    
    elif argv[0] == '--filter':
        _query = argv[1] # "oeuvre inconnue"
        _scope = argv[2] # "titles"
        zf = ZotFilter(_query, _scope)
        zf.filter()
    
    elif argv[0] == '--action':
        _key = argv[1] # '266264_JGI5I4TE'
        _action = argv[2] # 'open'
        za = ZotAction(_key, _action)
        za.act()
    






if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
