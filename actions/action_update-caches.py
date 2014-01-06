#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import json
import collections
import alp
import _mappings
from _zotquery import get_zotero_db, to_unicode

"""
This script works in 4 stages:
	1) create a JSON cache of your Zotero database
	2) create a JSON cache of your Zotero collections
	3) create a JSON cache of your Zotero tags
	4) merge all three JSON caches together to form the final JSON file.
	
It is necessary to work through these stages, versus creating a single database from the outset, because SQL only displays that items that meet all the criteria given. So a SQL query that gets id, type, creator info, field info, collection name, and tag name, will only return those items in your database that are in collections and have tags. This method creates three seperate caches, but ensures that your data is a robust as possible. 

All of the steps are wrapped in try-blocks, each of which has a unique log. So, if the script fails, you can isolate the issue. 
"""
	
### INITIAL SETUP

try:
	# Set path to Zotero sqlite database
	zotero_path = get_zotero_db()
except:
	alp.log("Setup Failed! Cannot locate Zotero database.")
	print "Setup Failed! Cannot locate Zotero database."

try:
	# Connect to Zotero database
	conn = sqlite3.connect(zotero_path)
	cur = conn.cursor()	
except:
	alp.log("Database Backup Failed! Zotero database locked.")
	print "Database Backup Failed! Zotero database locked."

try:
	# First create a list of deleted items, to ignore later
	deleted_query = "select itemID from deletedItems"
	dels = cur.execute(deleted_query).fetchall()
	deleted = []
	for item in dels:
		deleted.append(item[0])			
except:
	alp.log("Database Backup Failed! Script cannot access Zotero's deleted items.")
	print "Database Backup Failed! Script cannot access Zotero's deleted items."
	


### STEP ONE: CREATE DATABASE JSON
"""
This script creates a JSON cache of the pertinent information in the user's Zotero sqlite database. 
"""

try:		
	# This query retrieves tuples containing (id, type, last name, first name, creator type, field name, and field value) for each item in the user's Zotero database
	info_query = """
	select items.itemID, itemTypes.typeName, creatorData.lastName, creatorData.firstName, creatorTypes.creatorType, fields.fieldName, itemDataValues.value
		from items, itemTypes, creatorData, creatorTypes, fields,  itemDataValues, itemCreators, creators, itemData
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
except:
	alp.log("Database Backup Failed! Script cannot access Zotero's items.")
	print "Database Backup Failed! Script cannot access Zotero's items."
		
try:
	# Prepare list for the dictionary entries
	db_res = []
	# Prepare sub-list and sub-dictionary used in the algorithm below
	sub_data = {}
	sub_creator = []
	# Prepare lists to contain item ids, item types, and creator last names
	id_l = [] 
	type_l = []
	last_l = [] 
	
	for i, item in enumerate(info):
					
		if item[0] not in deleted:	
			# If first item
			if i == 0:
				
				# Create main 4 dictionaries: id, type, creator, and data
				id = {'id': to_unicode(item[0], encoding='utf-8')}
				id_l.append(id)
				
				# Uses the Zotero to CSL-JSON _mappings for item types
				csl_type = _mappings.trans_types(item[1])
				type = {'type':csl_type}
				type_l.append(type)
				
				# Uses the Zotero to CSL-JSON _mappings for creator types
				c_type = _mappings.trans_creators(item[4])
				creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[2], encoding='utf-8')), ('given', to_unicode(item[3], encoding='utf-8'))])
				last_l.append({'family':item[2]})
				# Add this item's creator to the sub_creator list
				sub_creator.append(creator)

				# Uses the Zotero to CSL-JSON _mappings for field names
				val = _mappings.trans_fields(item[5])
				if val == "issued":
					v = to_unicode(item[6][0:4], encoding='utf-8')
				else:
					v = to_unicode(item[6], encoding='utf-8')
				data = {val:v}
				# Add this item's data to the sub_data dictionary
				sub_data.update(data)
				
			# If not the last item
			elif i > 0 and i < (len(info) - 1):
					
				# Create main two dictionaries
				id = {'id': to_unicode(item[0], encoding='utf-8')}
					
				csl_type = _mappings.trans_types(item[1])
				type = {'type':csl_type}
					
				# If old id
				if id == id_l[-1]:
					
					# If old author
					if {'family':item[2]} == last_l[-1]:
					
						# Place metadata in the dictionary with proper keys
						val = _mappings.trans_fields(item[5])
						if val == "issued":
							v = to_unicode(item[6][0:4], encoding='utf-8')
						else:
							v = to_unicode(item[6], encoding='utf-8')
						data = {val:v}
						# Add this item's data to the sub_data dictionary
						sub_data.update(data)

					# If new author for old id
					else:
						c_type = _mappings.trans_creators(item[4])
						creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[2], encoding='utf-8')), ('given', to_unicode(item[3], encoding='utf-8'))])
						# Add this item's creator to the sub_creator list
						sub_creator.append(creator)
						last_l.append({'family':item[2]})
							
				# If new id
				else:
						
					# Add old data
					d = collections.OrderedDict()
					id1 = id_l.pop()
					d['id'] = id1['id']
					type1 = type_l.pop()
					d['type'] = type1['type']
					d['creators'] = sub_creator
					d['data'] = sub_data
					# These two lists will be filled later.
					d['zot-collections'] = []
					d['zot-tags'] = []
					db_res.append(d)
					
					# Restart all relevant lists
					id_l.append(id)	
					last_l.append({'family':item[2]})
					type_l.append(type)
					sub_data = {}
					sub_creator = []
						
					# Load data into lists	
					c_type = _mappings.trans_creators(item[4])
					creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[2], encoding='utf-8')), ('given', to_unicode(item[3], encoding='utf-8'))])
					# Add this item's creator to the sub_creator list
					sub_creator.append(creator)
						
					# Place metadata in the dictionary with proper keys
					val = _mappings.trans_fields(item[5])
					if val == "issued":
						v = to_unicode(item[6][0:4], encoding='utf-8')
					else:
						v = to_unicode(item[6], encoding='utf-8')
					data = {val:v}
					# Add this item's data to the sub_data dictionary
					sub_data.update(data)
				
			# If last item
			else:
				# Add old data
				d = collections.OrderedDict()
				id1 = id_l.pop()
				d['id'] = id1['id']
				type1 = type_l.pop()
				d['type'] = type1['type']	
				d['creators'] = sub_creator
				d['data'] = sub_data
				# These two lists will be filled later.
				d['zot-collections'] = []
				d['zot-tags'] = []
				db_res.append(d)	

	# Close sqlite connection
	conn.close()	
	
	# Log the results
	alp.log("Database Success! Completed backup of Zotero database.")
except:
	alp.log("Database Backup Failed! Script failed to render JSON.")
	print "Database Backup Failed! Script failed to render JSON."
	


### STEP TWO: CREATE COLLECTION JSON
"""
This script creates a cache of your Zotero collection data. 
"""

try:
	conn = sqlite3.connect(zotero_path)
	cur = conn.cursor()	
	# Retrieve collection data from Zotero database
	collection_query = """
			select items.itemID, collections.collectionName
			from items, collections, collectionItems
			where
				items.itemID = collectionItems.itemID
				and collections.collectionID = collectionItems.collectionID
			order by collections.collectionName
			"""
	colls = cur.execute(collection_query).fetchall()
except:
	alp.log("Collections Backup Failed! Script cannot access Zotero's collections.")
	print "Collections Backup Failed! Script cannot access Zotero's collections."

try:
	# Prepare lists
	coll_l = []
	sub = []
	coll_res = []
	for i, item in enumerate(colls):
		
		if item[0] not in deleted:
			# If first item
			if i == 0:
				sub.append(to_unicode(item[0], encoding='utf-8'))
				coll_l.append(item[1])
				
			# If not the last item
			elif i > 0 and i < (len(colls) - 1):
				
				# If old collection
				if item[1] == coll_l[-1]:
					sub.append(to_unicode(item[0], encoding='utf-8'))
					
				# If new collection
				else:
					# Add old data
					d = collections.OrderedDict()
					coll_name = coll_l.pop()
					d['zot-collection'] = to_unicode(coll_name, encoding='utf-8')
					d['items'] = sub
					coll_res.append(d)		
					
					# Restart all relevant lists
					sub = []
					
					# Load data into lists
					sub.append(to_unicode(item[0], encoding='utf-8'))
					coll_l.append(item[1])
			
			# If last item
			elif i == (len(colls) - 1):	
				d = collections.OrderedDict()
				coll_name = coll_l.pop()
				d['zot-collection'] = to_unicode(coll_name, encoding='utf-8')
				d['items'] = sub
				coll_res.append(d)	

	# Close sqlite connection
	conn.close()
	
	# Log the results
	alp.log("Collections Success! Completed json backup of Zotero collections data.")
except:
	alp.log("Collections Backup Failed! Script failed to render collection JSON.")
	print "Collections Backup Failed! Script failed to render collection JSON."
	


### STEP THREE: CREATE TAG JSON
"""
This script creates a cache of your Zotero tag data. 
"""

try:
	conn = sqlite3.connect(zotero_path)
	cur = conn.cursor()	
	tag_query = """
			select items.itemID, tags.name
			from items, tags, itemTags
			where
				items.itemID = itemTags.itemID
				and tags.tagID = itemTags.tagID
			order by tags.name
			"""
	tags = cur.execute(tag_query).fetchall()
except:
		alp.log("Tags Backup Failed! Script cannot access Zotero's tags.")
		print "Tags Backup Failed! Script cannot access Zotero's tags."

try:
	l = []
	sub = []
	tag_res = []
	for i, item in enumerate(tags):
		
		if item[0] not in deleted:
		
			# If first item
			if i == 0:
				sub.append(to_unicode(item[0], encoding='utf-8'))
				l.append(item[1])
			
			# If not the last item
			elif i > 0 and i < (len(tags) - 1):
				
				# If old collection
				if item[1] == l[-1]:
					sub.append(to_unicode(item[0], encoding='utf-8'))
				# If new collection
				else:
					# Add old data
					d = collections.OrderedDict()
					tag_name = l.pop()
					d['zot-tag'] = to_unicode(tag_name, encoding='utf-8')
					d['items'] = sub
					tag_res.append(d)	
					
					# Restart all relevant lists
					sub = []
					
					# Load data into lists
					sub.append(to_unicode(item[0], encoding='utf-8'))
					l.append(item[1])
					
			# If last item
			elif i == (len(tags) - 1):	
				d = collections.OrderedDict()
				tag_name = l.pop()
				d['zot-tag'] = to_unicode(tag_name, encoding='utf-8')
				d['items'] = sub
				tag_res.append(d)
		
	conn.close()
	
	# Log the results
	alp.log("Tags Success! Completed json backup of Zotero tags data.")
except:
	alp.log("Tags Backup Failed! Script failed to render tags JSON.")
	print "Tags Backup Failed! Script failed to render tags JSON."



### STEP FOUR: MERGE ALL THREE JSON FILES TOGETHER
"""
This script merges the Collection and Tag information with your primary Zotero JSON file.
"""

try: 
	for i, item in enumerate(db_res):
		for j, jtem in enumerate(coll_res):
			if item['id'] in jtem['items']:
				item['zot-collections'].append(jtem['zot-collection'])
				
				
	for i, item in enumerate(db_res):
		for j, jtem in enumerate(tag_res):
			if item['id'] in jtem['items']:
				item['zot-tags'].append(jtem['zot-tag'])
except:
	alp.log("Final Backup Failed! Script failed to merge dictionaries.")
	print "Final Backup Failed! Script failed to merge dictionaries."

try:				
	final_json = json.dumps(db_res, sort_keys=False, indent=4, separators=(',', ': '))

	# Write final, formatted json to Alfred cache
	cache = alp.cache(join='zotero_db.json')
	cache_file = open(cache, 'w+')
	cache_file.write(final_json.encode('utf-8'))
	cache_file.close()
	
	# Log the result
	alp.log("Final Success! Created JSON cache of Zotero database.")
	print "Final Success! Created JSON cache of Zotero database."
except:
	alp.log("Final Backup Failed! Script failed to render final JSON.")
	print "Final Backup Failed! Script failed to render final JSON."