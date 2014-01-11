#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import sqlite3
import json
import collections
import os
import sys
import shutil
import _mappings
from _zotquery import get_zotero_db, to_unicode, check_cache, get_zotero_storage, get_zotero_basedir

"""
This script works in 4 stages:
	1) create a JSON cache of your Zotero database
	2) create a JSON cache of your Zotero collections
	3) create a JSON cache of your Zotero tags
	4) merge all three JSON caches together to form the final JSON file.
	
It is necessary to work through these stages, versus creating a single database from the outset, 
because SQL only displays that items that meet all the criteria given. 
So a SQL query that gets id, type, creator info, field info, collection name, and tag name, 
will only return those items in your database that are in collections and have tags. 
This method creates three seperate caches, but ensures that your data is a robust as possible. 

All of the steps are wrapped in try-blocks, each of which has a unique log. 
So, if the script fails, you can isolate the issue. 
"""
	
### INITIAL SETUP
# Only update if needed
#force = sys.argv[1]
force = True

if check_cache() or force:
	# Log start time
	alp.log('START: update cache process.')
	try:
		# Create a copy of the user's Zotero database 
		zotero_path = get_zotero_db()
		clone_database = os.path.join(alp.cache(), "zotquery.sqlite")
		shutil.copyfile(zotero_path, clone_database)
	
		try:
			# Connect to Zotero clone database
			conn = sqlite3.connect(clone_database)
			cur = conn.cursor()	

			try:
				# First create a list of deleted items, to ignore later
				deleted_query = "select itemID from deletedItems"
				dels = cur.execute(deleted_query).fetchall()
				deleted = []
				for item in dels:
					deleted.append(item[0])			
			

				### STEP ONE: CREATE DATABASE DICTIONARIES
				"""
				This part of the script creates an array of the pertinent information in the user's Zotero sqlite database. 
				"""
				try:		
					# This query retrieves tuples containing (id, type, last name, first name, creator type, field name, and field value) for each item in the user's Zotero database
					info_query = """
					select items.itemID, items.key, itemTypes.typeName, creatorData.lastName, creatorData.firstName, creatorTypes.creatorType, fields.fieldName, itemDataValues.value
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
					
					try:
						# Prepare list for the dictionary entries
						db_res = []
						# Prepare sub-list and sub-dictionary used in the algorithm below
						sub_data = {}
						sub_creator = []
						# Prepare lists to contain item ids, item keys, item types, and creator last names
						id_l = [] 
						key_l = []
						type_l = []
						last_l = [] 
						
						for i, item in enumerate(info):
										
							if item[0] not in deleted:	
								# If first item
								if i == 0:
									
									# Create main 5 dictionaries: id, key, type, creator, and data
									id = {'id': to_unicode(item[0], encoding='utf-8')}
									id_l.append(id)

									key = {'key': to_unicode(item[1], encoding='utf-8')}
									key_l.append(key)
									
									# Uses the Zotero to CSL-JSON _mappings for item types
									csl_type = _mappings.trans_types(item[2])
									type = {'type':csl_type}
									type_l.append(type)
									
									# Uses the Zotero to CSL-JSON _mappings for creator types
									c_type = _mappings.trans_creators(item[5])
									creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[3], encoding='utf-8')), ('given', to_unicode(item[4], encoding='utf-8'))])
									last_l.append({'family':item[3]})
									# Add this item's creator to the sub_creator list
									sub_creator.append(creator)

									# Uses the Zotero to CSL-JSON _mappings for field names
									val = _mappings.trans_fields(item[6])
									if val == "issued":
										v = to_unicode(item[7][0:4], encoding='utf-8')
									else:
										v = to_unicode(item[7], encoding='utf-8')
									data = {val:v}
									# Add this item's data to the sub_data dictionary
									sub_data.update(data)
									
								# If not the last item
								elif i > 0 and i < (len(info) - 1):
										
									# Create main three dictionaries
									id = {'id': to_unicode(item[0], encoding='utf-8')}

									key = {'key': to_unicode(item[1], encoding='utf-8')}
										
									type = {'type':_mappings.trans_types(item[2])}
										
									# If old id
									if id == id_l[-1]:
										
										# If old author
										if {'family':item[3]} == last_l[-1]:
										
											# Place metadata in the dictionary with proper keys
											val = _mappings.trans_fields(item[6])
											if val == "issued":
												v = to_unicode(item[7][0:4], encoding='utf-8')
											else:
												v = to_unicode(item[7], encoding='utf-8')
											data = {val:v}
											# Add this item's data to the sub_data dictionary
											sub_data.update(data)

										# If new author for old id
										else:
											c_type = _mappings.trans_creators(item[5])
											creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[3], encoding='utf-8')), ('given', to_unicode(item[4], encoding='utf-8'))])
											# Add this item's creator to the sub_creator list
											sub_creator.append(creator)
											last_l.append({'family':item[3]})
												
									# If new id
									else:
											
										# Add old data
										d = collections.OrderedDict()
										id1 = id_l.pop()
										d['id'] = id1['id']
										key1 = key_l.pop()
										d['key'] = key1['key']
										type1 = type_l.pop()
										d['type'] = type1['type']
										d['creators'] = sub_creator
										d['data'] = sub_data
										# These two lists will be filled later.
										d['zot-collections'] = []
										d['zot-tags'] = []
										d['attachments'] = []
										db_res.append(d)
										
										# Restart all relevant lists
										id_l.append(id)	
										key_l.append(key)
										last_l.append({'family':item[3]})
										type_l.append(type)
										sub_data = {}
										sub_creator = []
											
										# Load data into lists	
										c_type = _mappings.trans_creators(item[5])
										creator = collections.OrderedDict([('type', c_type), ('family', to_unicode(item[3], encoding='utf-8')), ('given', to_unicode(item[4], encoding='utf-8'))])
										# Add this item's creator to the sub_creator list
										sub_creator.append(creator)
											
										# Place metadata in the dictionary with proper keys
										val = _mappings.trans_fields(item[6])
										if val == "issued":
											v = to_unicode(item[7][0:4], encoding='utf-8')
										else:
											v = to_unicode(item[7], encoding='utf-8')
										data = {val:v}
										# Add this item's data to the sub_data dictionary
										sub_data.update(data)
									
								# If last item
								else:
									# Add old data
									d = collections.OrderedDict()
									id1 = id_l.pop()
									d['id'] = id1['id']
									key1 = key_l.pop()
									d['key'] = key1['key']
									type1 = type_l.pop()
									d['type'] = type1['type']	
									d['creators'] = sub_creator
									d['data'] = sub_data
									# These two lists will be filled later.
									d['zot-collections'] = []
									d['zot-tags'] = []
									d['attachments'] = []
									db_res.append(d)	

						# Close sqlite connection
						conn.close()	
						# Log the results
						alp.log("Database Success! Completed backup of Zotero database.")
					
			
						### STEP TWO: CREATE COLLECTION DICTIONARIES
						"""
						This part of the script creates a cache of your Zotero collection data. 
						"""
						try:
							conn = sqlite3.connect(clone_database)
							cur = conn.cursor()	
							# Retrieve collection data from Zotero database
							collection_query = """
									select items.itemID, collections.collectionName, collections.key
									from items, collections, collectionItems
									where
										items.itemID = collectionItems.itemID
										and collections.collectionID = collectionItems.collectionID
									order by collections.key
									"""
							colls = cur.execute(collection_query).fetchall()
						
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
											coll_l.append([item[1], item[2]])
											
										# If not the last item
										elif i > 0 and i < (len(colls) - 1):
											
											# If old collection
											if item[1] == coll_l[-1][0]:
												sub.append(to_unicode(item[0], encoding='utf-8'))
												
											# If new collection
											else:
												# Add old data
												d = collections.OrderedDict()
												coll = coll_l.pop()
												d['zot-collection'] = {'name': to_unicode(coll[0], encoding='utf-8'), 'key': to_unicode(coll[1], encoding='utf-8')}
												d['items'] = sub
												coll_res.append(d)		
												
												# Restart relevant list
												sub = []
												
												# Load data into lists
												sub.append(to_unicode(item[0], encoding='utf-8'))
												coll_l.append([item[1], item[2]])
										
										# If last item
										elif i == (len(colls) - 1):	
											d = collections.OrderedDict()
											coll = coll_l.pop()
											d['zot-collection'] = {'name': to_unicode(coll[0], encoding='utf-8'), 'key': to_unicode(coll[1], encoding='utf-8')}
											d['items'] = sub
											coll_res.append(d)	

								# Close sqlite connection
								conn.close()
								# Log the results
								alp.log("Collections Success! Completed json backup of Zotero collections data.")
							

								### STEP THREE: CREATE TAG DICTIONARIES
								"""
								This part of the script creates a cache of your Zotero tag data. 
								"""
								try:
									conn = sqlite3.connect(clone_database)
									cur = conn.cursor()	
									tag_query = """
											select items.itemID, tags.name, tags.key
											from items, tags, itemTags
											where
												items.itemID = itemTags.itemID
												and tags.tagID = itemTags.tagID
											order by tags.key
											"""
									tags = cur.execute(tag_query).fetchall()
								
									try:
										tag_l = []
										sub = []
										tag_res = []
										for i, item in enumerate(tags):
											
											if item[0] not in deleted:
											
												# If first item
												if i == 0:
													sub.append(to_unicode(item[0], encoding='utf-8'))
													tag_l.append([item[1], item[2]])
												
												# If not the last item
												elif i > 0 and i < (len(tags) - 1):
													
													# If old collection
													if item[1] == tag_l[-1][0]:
														sub.append(to_unicode(item[0], encoding='utf-8'))
													# If new collection
													else:
														# Add old data
														d = collections.OrderedDict()
														tag = tag_l.pop()
														d['zot-tag'] = {'name': to_unicode(tag[0], encoding='utf-8'), 'key': to_unicode(tag[1], encoding='utf-8')}
														d['items'] = sub
														tag_res.append(d)	
														
														# Restart all relevant lists
														sub = []
														
														# Load data into lists
														sub.append(to_unicode(item[0], encoding='utf-8'))
														tag_l.append([item[1], item[2]])
														
												# If last item
												elif i == (len(tags) - 1):	
													d = collections.OrderedDict()
													tag = tag_l.pop()
													d['zot-tag'] = {'name': to_unicode(tag[0], encoding='utf-8'), 'key': to_unicode(tag[1], encoding='utf-8')}
													d['items'] = sub
													tag_res.append(d)
											
										conn.close()
										# Log the results
										alp.log("Tags Success! Completed json backup of Zotero tags data.")
									

										### STEP FOUR: CREATE ATTACHMENT DICTIONARIES
										try:
											# These extensions are recognized as fulltext attachments
											attachment_ext = [".pdf", "epub"]

											conn = sqlite3.connect(clone_database)
											cur = conn.cursor()	
											# Retrieve attachment data from Zotero database
											attachment_query = """
												select items.itemID, itemAttachments.path, itemAttachments.itemID
												from items, itemAttachments
												where items.itemID = itemAttachments.sourceItemID
												"""
											# Retrieve attachments
											attachments = cur.execute(attachment_query).fetchall()

											try:
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
																storage_path = get_zotero_storage()
																base = os.path.join(storage_path, key).encode('utf-8')
																att_path = os.path.join(base, item_attachment).encode('utf-8')

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
																base = get_zotero_basedir()
																att_path = os.path.join(base, link_attachment).encode('utf-8')

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

												conn.close()
												# Log the results
												alp.log("Attachements Success! Completed backup of Zotero attachment data.")


												### STEP FIVE: MERGE ALL FOUR DICTIONARIES TOGETHER
												try: 
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
												
													try:				
														final_json = json.dumps(db_res, sort_keys=False, indent=4, separators=(',', ': '))

														# Write final, formatted json to Alfred cache
														cache = alp.cache(join='zotero_db.json')
														cache_file = open(cache, 'w+')
														cache_file.write(final_json.encode('utf-8'))
														cache_file.close()
														
														#print final_json

														# Log the result
														alp.log("Final Success! Created JSON cache of Zotero database.")
														print "Final Success! Created JSON cache of Zotero database."
													except:
														alp.log("Final Backup Failed! Script failed to render and write final JSON.")
														print "Final Backup Failed! Script failed to render and write final JSON."
												except:
													alp.log("Final Backup Failed! Script failed to merge dictionaries.")
													print "Final Backup Failed! Script failed to merge dictionaries."
											except:
												alp.log("Attachment Backup Failed! Script failed to create attachment dictionaries.")
												print "Attachment Backup Failed! Script failed to create attachment dictionaries."
										except:
											alp.log("Attachment Backup Failed! Script cannot access Zotero's attachments")
											print "Attachment Backup Failed! Script cannot access Zotero's attachments"
									except:
										alp.log("Tags Backup Failed! Script failed to create tags dictionaries.")
										print "Tags Backup Failed! Script failed to create tags dictionaries."
								except:
									alp.log("Tags Backup Failed! Script cannot access Zotero's tags.")
									print "Tags Backup Failed! Script cannot access Zotero's tags."
							except:
								alp.log("Collections Backup Failed! Script failed to create collection dictionaries.")
								print "Collections Backup Failed! Script failed to create collection dictionaries."
						except:
							alp.log("Collections Backup Failed! Script cannot access Zotero's collections.")
							print "Collections Backup Failed! Script cannot access Zotero's collections."
					except:
						alp.log("Database Backup Failed! Script failed to create item info dictionaries.")
						print "Database Backup Failed! Script failed to create item info dictionaries."
				except:
					alp.log("Database Backup Failed! Script cannot access Zotero's items.")
					print "Database Backup Failed! Script cannot access Zotero's items."
			except:
				alp.log("Database Backup Failed! Script cannot access Zotero's deleted items.")
				print "Database Backup Failed! Script cannot access Zotero's deleted items."
		except:
			alp.log("Database Backup Failed! Zotero clone database locked.")
			print "Database Backup Failed! Zotero clone database locked."
	except:
		alp.log("Setup Failed! Cannot locate and clone Zotero database.")
		print "Setup Failed! Cannot locate and clone Zotero database."
else:
	alp.log("Cache already up-to-date.")
	print "Cache already up-to-date."

# Log finish time
alp.log('END: update cache process.')