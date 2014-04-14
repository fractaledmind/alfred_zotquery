#!/usr/bin/python
# encoding: utf-8
import sys
sys.path.insert(0, "alfred-workflow.zip")
import workflow
import os.path
import sqlite3
import json
from collections import OrderedDict
import shutil
import zq_utils as z
from zq_utils import to_unicode as uni
from dependencies import applescript

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
        self.wf = workflow.Workflow()

        self.zot_db = self.get_path('database_path')
        self.json_db = self.wf.datafile("zotero_db.json")
        self.clone_db = self.wf.datafile("zotquery.sqlite")
        self.backup_db = self.wf.datafile("old_db.json")

        self.conn = sqlite3.connect(self.zot_db)
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
            if self.force == True or z.check_cache()[0]:     
                shutil.copyfile(self.zot_db, self.clone_db)
                return True
            else:
                return False

        # Not configured
        else:
            a_script = """
                tell application "Alfred 2" to search "z:config"
            """
            applescript.asrun(a_script)
            return False


    def get_path(self, _type): 
        """Read paths.json file from non-volatile storage"""

        with open(self.wf.datafile("paths.json"), 'r') as f:
            _paths = json.load(f)
            f.close()
        return uni(_paths[_type])


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

        info_sql = """SELECT key, itemID, itemTypeID
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
        """Convert Zotero .sqlite database to JSON file"""
        # adapted from:
        # https://github.com/pkeane/zotero_hacks
        _items = []
        basic_info = self.info_query()

        for basic in basic_info:
            # prepare item's base dict and data dict
            item_dict = OrderedDict()
            item_meta = OrderedDict()

            item_key = item_id = item_type_id = ''
            (item_key, item_id, item_type_id) = basic
            item_dict['key'] = item_key

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
                    (first_name,last_name, c_type) = creator_info
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
                        if field_name == 'issued':
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

            #####
            _items.append(item_dict)

        final_json = json.dumps(_items, sort_keys=False, indent=4, separators=(',', ': '))
        self.sqlite_close()

        return final_json



################################################################################
### Main Function                                                            ###
################################################################################

def main(wf):
    """Retrieve note data from Zotero sqlite database"""

    cacher = ZotCache(True, False)
    print cacher.cache().encode('utf-8')



if __name__ == '__main__':
    wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
    sys.exit(wf.run(main))
