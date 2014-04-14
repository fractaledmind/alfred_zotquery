#!/usr/bin/python
# encoding: utf-8
import sys
sys.path.insert(0, 'alfred-workflow.zip')
import workflow
import os.path

def main(wf):
    import sqlite3
    import json
    import collections
    import shutil
    import _mappings
    import zq_utils as z
    from zq_utils import to_unicode as uni
    import applescript

    """
    This script works in 5 stages:
        1) create a JSON cache of your Zotero database
        2) create a JSON cache of your Zotero collections
        3) create a JSON cache of your Zotero tags
        4) create a JSON cache of your Zotero attachments
        5) create a JSON cache of your Zotero notes
        6) merge all four JSON caches together to form the final JSON file.
        
    It is necessary to work through these stages, 
    versus creating a single database from the outset, 
    because SQL only displays that items that meet all the criteria given. 
    This method ensures that your data is a robust as possible.
    """
        
    # First, ensure that Configuration has taken place
    if os.path.exists(wf.datafile("first-run.txt")):

        ### INITIAL SETUP
        # Only update if needed
        #force = wf.args[0]
        #personal_only = wf.args[1]
        personal_only = True
        force = 'True'
        ### Back-up old Cache
        if os.path.exists(wf.datafile("zotero_db.json")):
            shutil.copyfile(wf.datafile("zotero_db.json"), wf.datafile("old_db.json"))

        ### Begin new cache
        if force == 'True' or z.check_cache()[0]:     
            # Create a copy of the user's Zotero database 
            zotero_path = z.get_path('database_path')
            clone_database = wf.datafile("zotquery.sqlite")
            shutil.copyfile(zotero_path, clone_database)
            
            # Connect to Zotero clone database
            conn = sqlite3.connect(clone_database)
            cur = conn.cursor() 

            ### STEP ONE: CREATE DATABASE DICTIONARIES  
            # This query retrieves tuples containing 
            # (id, type, last, first, creator type, field name, and value) 
            # for each item in the user's Zotero database
            info_query = """
                select items.itemID, items.key, itemTypes.typeName, creatorData.lastName, 
                creatorData.firstName, creatorTypes.creatorType, fields.fieldName, itemDataValues.value
                from items, itemTypes, creatorData, creatorTypes, fields, 
                itemDataValues, itemCreators, creators, itemData
                where
                    items.itemID = itemData.itemID
                    and itemData.fieldID = fields.fieldID
                    and itemData.valueID = itemDataValues.valueID
                    and items.itemTypeID = itemTypes.itemTypeID
                    and itemCreators.creatorTypeID = creatorTypes.creatorTypeID
                    and items.itemID = itemCreators.itemID
                    and itemCreators.creatorID = creators.creatorID
                    and creators.creatorDataID = creatorData.creatorDataID
                    and itemCreators.creatorTypeID = creatorTypes.creatorTypeID
                    and itemTypes.typeName != "attachment"
                order by items.itemID
            """
            # Retrieve data from Zotero database
            info = cur.execute(info_query).fetchall()   
            
            # Prepare list for the dictionary entries
            db_res = []
            # Prepare sub-list and sub-dictionary used in the algorithm below
            sub_data = {}
            sub_creator = []
            # Prepare lists to contain 
            # item ids, item keys, item types, and creator last names
            id_l = [] 
            key_l = []
            type_l = []
            last_l = [] 
            
            # Prepare mappings object
            _mp = _mappings.ZotMap()
            for i, item in enumerate(info):
                if i == 0:
                    _id = {'id': uni(item[0])}
                    id_l.append(_id)
                    key = {'key': uni(item[1])}
                    key_l.append(key)
                
                    # Uses the Zotero to CSL-JSON _mappings for item types
                    csl_type = _mp.trans_types(item[2], 'csl')
                    _type = {'type':csl_type}
                    type_l.append(_type)
                
                    # Uses the Zotero to CSL-JSON _mp for creator types
                    c_type = _mp.trans_creators(item[5], 'csl')
                    creator = collections.OrderedDict([('type', c_type), 
                        ('family', uni(item[3])), 
                        ('given', uni(item[4]))])
                    last_l.append({'family':item[3]})
                    # Add this item's creator to the sub_creator list
                    sub_creator.append(creator)

                    # Uses the Zotero to CSL-JSON _mp for field names
                    val = _mp.trans_fields(item[6], 'csl')
                    if val == "issued":
                        _val = uni(item[7][0:4])
                    else:
                        _val = uni(item[7])
                    data = {val:_val}
                    # Add this item's data to the sub_data dictionary
                    sub_data.update(data)
                    
                # If not the last item
                elif i > 0 and i < (len(info) - 1):
                    _id = {'id': uni(item[0])}
                    _key = {'key': uni(item[1])}
                    _type = {'type':_mp.trans_types(item[2], 'csl')}
                    
                    # If old id
                    if _id == id_l[-1]:
                    
                        # If old author
                        if {'family':item[3]} == last_l[-1]:
                    
                            # Place metadata in the dictionary with proper keys
                            val = _mp.trans_fields(item[6], 'csl')
                            if val == "issued":
                                _val = uni(item[7][0:4])
                            else:
                                _val = uni(item[7])
                            _data = {val:_val}
                            # Add this item's data to the sub_data dictionary
                            sub_data.update(_data)

                        # If new author for old id
                        else:
                            c_type = _mp.trans_creators(item[5], 'csl')
                            creator = collections.OrderedDict([('type', c_type), 
                                ('family', uni(item[3])), 
                                ('given', uni(item[4]))])
                            # Add this item's creator to the sub_creator list
                            sub_creator.append(creator)
                            last_l.append({'family':item[3]})
                            
                    # If new id
                    else:
                        # Add old data
                        _dict = collections.OrderedDict()
                        id1 = id_l.pop()
                        _dict['id'] = id1['id']
                        key1 = key_l.pop()
                        _dict['key'] = key1['key']
                        type1 = type_l.pop()
                        _dict['type'] = type1['type']
                        _dict['creators'] = sub_creator
                        _dict['data'] = sub_data
                        # These two lists will be filled later.
                        _dict['zot-collections'] = []
                        _dict['zot-tags'] = []
                        _dict['attachments'] = []
                        _dict['notes'] = []
                        db_res.append(_dict)
                    
                        # Restart all relevant lists
                        id_l.append(_id) 
                        key_l.append(_key)
                        last_l.append({'family':item[3]})
                        type_l.append(_type)
                        sub_data = {}
                        sub_creator = []
                        
                        # Load data into lists  
                        c_type = _mp.trans_creators(item[5], 'csl')
                        creator = collections.OrderedDict([('type', c_type), 
                            ('family', uni(item[3])), 
                            ('given', uni(item[4]))])
                        # Add this item's creator to the sub_creator list
                        sub_creator.append(creator)
                        
                        # Place metadata in the dictionary with proper keys
                        val = _mp.trans_fields(item[6], 'csl')
                        if val == "issued":
                            _val = uni(item[7][0:4])
                        else:
                            _val = uni(item[7])
                        _data = {val:_val}
                        # Add this item's data to the sub_data dictionary
                        sub_data.update(_data)
                
                # If last item
                else:
                    _dict = collections.OrderedDict()
                    id1 = id_l.pop()
                    _dict['id'] = id1['id']
                    key1 = key_l.pop()
                    _dict['key'] = key1['key']
                    type1 = type_l.pop()
                    _dict['type'] = type1['type']   
                    _dict['creators'] = sub_creator
                    _dict['data'] = sub_data
                    # These two lists will be filled later.
                    _dict['zot-collections'] = []
                    _dict['zot-tags'] = []
                    _dict['attachments'] = []
                    _dict['notes'] = []
                    db_res.append(_dict)    


            ### STEP TWO: CREATE COLLECTION DICTIONARIES
            ## 2.1 Personal Collections
            # Retrieve collection data from Zotero database
            collection_query = """
                select items.itemID, collections.collectionName, collections.key
                from items, collections, collectionItems
                where
                    items.itemID = collectionItems.itemID
                    and collections.collectionID = collectionItems.collectionID
                    and collections.libraryID is null
                order by collections.key
            """
            colls = cur.execute(collection_query).fetchall()

            # Prepare lists
            coll_l = []
            sub = []
            coll_res = []
            for i, item in enumerate(colls):
                # If first item
                if i == 0:
                    sub.append(uni(item[0]))
                    coll_l.append(item[1:])
                    
                # If not the last item
                elif i > 0 and i < (len(colls) - 1):
                    if item[1] == coll_l[-1][0]:
                        sub.append(uni(item[0]))
                    
                    # If new collection
                    else:
                        # Add old data
                        d = collections.OrderedDict()
                        coll = coll_l.pop()
                        d['zot-collection'] = {'name': uni(coll[0]), 'key': uni(coll[1]), 'group': 'personal', 'library_id': '0'}
                        d['items'] = sub
                        coll_res.append(d)      
                        # Restart relevant list
                        sub = []
                        # Load data into lists
                        sub.append(uni(item[0]))
                        coll_l.append(item[1:])
            
                # If last item
                elif i == (len(colls) - 1):
                    d = collections.OrderedDict()
                    coll = coll_l.pop()
                    d['zot-collection'] = {'name': uni(coll[0]), 'key': uni(coll[1]), 'group': 'personal', 'library_id': '0'}
                    d['items'] = sub
                    coll_res.append(d)  


            print coll_res
            return coll_res
            if personal_only == 'False':
                ## 2.2 Group Collections
                group_query = """
                    select items.itemID, collections.collectionName, collections.key, groups.name, groups.libraryID
                    from items, collections, collectionItems, groups
                    where
                        items.itemID = collectionItems.itemID
                        and collections.collectionID = collectionItems.collectionID
                        and collections.libraryID = groups.libraryID
                    order by collections.key
                """
                groups = cur.execute(group_query).fetchall()

                # Prepare lists
                group_l = []
                sub = []
                for i, item in enumerate(groups):

                    # If first item
                    if i == 0:
                        sub.append(uni(item[0]))
                        group_l.append(item[1:])
                        
                    # If not the last item
                    elif i > 0 and i < (len(groups) - 1):
                        if item[1] == group_l[-1][0]:
                            sub.append(uni(item[0]))
                        
                        # If new collection
                        else:
                            # Add old data
                            d = collections.OrderedDict()
                            coll = group_l.pop()
                            d['zot-collection'] = {'name': uni(coll[0]), 'key': uni(coll[1]), 'group': uni(coll[2]), 'library_id': uni(coll[3])}
                            d['items'] = sub
                            coll_res.append(d)      
                            # Restart relevant list
                            sub = []
                            # Load data into lists
                            sub.append(uni(item[0]))
                            group_l.append(item[1:])
                
                    # If last item
                    elif i == (len(colls) - 1):
                        d = collections.OrderedDict()
                        coll = group_l.pop()
                        d['zot-collection'] = {'name': uni(coll[0]), 'key': uni(coll[1]), 'group': uni(coll[2]), 'library_id': uni(coll[3])}
                        d['items'] = sub
                        coll_res.append(d)
            else:
                pass


            ### STEP THREE: CREATE TAG DICTIONARIES
            tag_query = """
                select items.itemID, tags.name, tags.key
                from items, tags, itemTags
                where
                    items.itemID = itemTags.itemID
                    and tags.tagID = itemTags.tagID
                order by tags.key
            """
            tags = cur.execute(tag_query).fetchall()

            tag_l = []
            sub = []
            tag_res = []
            for i, item in enumerate(tags):
                # If first item
                if i == 0:
                    sub.append(uni(item[0]))
                    tag_l.append([item[1], item[2]])
                
                # If not the last item
                elif i > 0 and i < (len(tags) - 1):
                    if item[1] == tag_l[-1][0]:
                        sub.append(uni(item[0]))
                    # If new collection
                    else:
                        # Add old data
                        d = collections.OrderedDict()
                        tag = tag_l.pop()
                        d['zot-tag'] = {'name': uni(tag[0]), 'key': uni(tag[1])}
                        d['items'] = sub
                        tag_res.append(d)   
                    
                        # Restart all relevant lists
                        sub = []
                    
                        # Load data into lists
                        sub.append(uni(item[0]))
                        tag_l.append([item[1], item[2]])
                    
                # If last item
                elif i == (len(tags) - 1):
                    d = collections.OrderedDict()
                    tag = tag_l.pop()
                    d['zot-tag'] = {'name': uni(tag[0]), 'key': uni(tag[1])}
                    d['items'] = sub
                    tag_res.append(d)
                
            
            ### STEP FOUR: CREATE ATTACHMENT DICTIONARIES
            # These extensions are recognized as fulltext attachments
            attachment_ext = [".pdf", "epub"]

            # Retrieve attachment data from Zotero database
            attachment_query = """
                select items.itemID, itemAttachments.path, itemAttachments.itemID
                from items, itemAttachments
                where items.itemID = itemAttachments.sourceItemID
            """
            # Retrieve attachments
            attachments = cur.execute(attachment_query).fetchall()

            att_res = []
            for item in attachments:
                item_id = item[0]
                
                if item[1] != None:
                    att = item[1]
                    # If the attachment is stored in the Zotero folder, 
                    # it is preceded by "storage:"
                    if att[:8] == "storage:":
                        item_attachment = att[8:]
                        attachment_id = item[2]
                        if item_attachment[-4:].lower() in attachment_ext:
                            cur.execute("select items.key from items where itemID = %d" % attachment_id)
                            key = cur.fetchone()[0]
                            storage_path = z.get_path('storage_path')
                            base = os.path.join(storage_path, key)
                            att_path = os.path.join(base, item_attachment)

                            d = collections.OrderedDict()
                            d['attachment'] = {'name': item_attachment, 'key': key, 'path': att_path}
                            d['item'] = item_id
                            att_res.append(d)

                    # If the attachment is linked to a location, 
                    # it is preceded by "attachments:"
                    elif att[:12] == "attachments:":
                        link_attachment = att[12:]
                        attachment_id = item[2]
                        if link_attachment[-4:].lower() in attachment_ext:
                            cur.execute("select items.key from items where itemID = %d" % attachment_id)
                            key = cur.fetchone()[0]
                            base = z.get_path('link-attachments_path')
                            att_path = os.path.join(base, link_attachment)

                            d = collections.OrderedDict()
                            d['attachment'] = {'name': link_attachment, 'key': key, 'path': att_path}
                            d['item'] = item_id
                            att_res.append(d)

                    # Else, there is simply the full path to the attachment
                    else:
                        item_attachment = att
                        name = item_attachment.split('/')[-1]
                        
                        d = collections.OrderedDict()
                        d['attachment'] = {'name': name, 'key': None, 'path': item_attachment}
                        d['item'] = item_id
                        att_res.append(d)


            ### STEP FIVE: CREATE NOTES DICTIONARIES
            notes_query = """
                select items.itemID, itemNotes.note
                from items, itemNotes
                where items.itemID = itemNotes.sourceItemID
                order by items.itemID
            """
            # Retrieve data from Zotero database
            notes = cur.execute(notes_query).fetchall() 
            conn.close()


            ### STEP SIX: MERGE ALL FOUR DICTIONARIES TOGETHER
            for item in db_res:
                for jtem in coll_res:
                    if item['id'] in jtem['items']:
                        item['zot-collections'].append(jtem['zot-collection'])
                                        
            for item in db_res:
                for jtem in tag_res:
                    if item['id'] in jtem['items']:
                        item['zot-tags'].append(jtem['zot-tag'])

            for item in db_res:
                for jtem in att_res:
                    if item['id'] == jtem['item']:
                        item['attachments'].append(jtem['attachment'])

            for item in db_res:
                for jtem in notes:
                    if item['id'] == jtem[0]:
                        item['notes'].append(jtem[1][33:-10])
                    
            final_json = json.dumps(db_res, sort_keys=False, indent=4, separators=(',', ': '))

            # Write final, formatted json to Alfred cache
            with open(wf.datafile("zotero_db.json"), 'w') as f:
                f.write(final_json.encode('utf-8'))
                f.close()
            
            #print final_json
            print "Cache Success!"
                
        else:
            print "Cache already up-to-date."
        

    # Not configured
    else:
        print "ZotQuery not yet configured"
        a_script = """
            tell application "Alfred 2" to search "z:config"
            """
        applescript.asrun(a_script)

if __name__ == '__main__':
    wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
    sys.exit(wf.run(main))