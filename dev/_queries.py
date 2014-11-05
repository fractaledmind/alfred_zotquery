#!/usr/bin/env python
# -*- coding: utf-8 -*-
import alp
import sqlite3

clone_database = alp.storage(join="zotquery.sqlite")
conn = sqlite3.connect(clone_database)
cur = conn.cursor()	

#query = 'sem'

def title(query): 
	title_query = """
	select items.key
	from items, itemData, fields, itemDataValues, itemTypes
	where
		items.itemID = itemData.itemID
		and itemData.fieldID = fields.fieldID
		and itemData.valueID = itemDataValues.valueID
		and items.itemTypeID = itemTypes.itemTypeID
		and itemTypes.typeName != "attachment"
		and (fields.fieldName = "title"
			or fields.fieldName = "publicationTitle"
			or fields.fieldName = "seriesTitle"
			or fields.fieldName = "series")
		and itemDataValues.value LIKE '%{0}%'
	""".format(query)
	title_info = cur.execute(title_query).fetchall()
	
	keys_list = []
	for item in title_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def author(query):
	author_query = """
		select items.key
			from items, creatorData, creatorTypes, itemCreators, creators
			where
				itemCreators.creatorTypeID = creatorTypes.creatorTypeID
				and items.itemID = itemCreators.itemID
				and itemCreators.creatorID = creators.creatorID
				and creators.creatorDataID = creatorData.creatorDataID
				and itemCreators.creatorTypeID = creatorTypes.creatorTypeID
				and creatorData.lastName LIKE '%{0}%'
		""".format(query)
	author_info = cur.execute(author_query).fetchall()

	keys_list = []
	for item in author_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def collection(query):
	collection_query = """
		select items.key
		from items, collections, collectionItems
		where
			items.itemID = collectionItems.itemID
			and collections.collectionID = collectionItems.collectionID
			and collections.collectionName LIKE '%{0}%'
		""".format(query)
	collection_info = cur.execute(collection_query).fetchall()

	keys_list = []
	for item in collection_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def tag(query):
	tag_query = """
			select items.key
			from items, tags, itemTags
			where
				items.itemID = itemTags.itemID
				and tags.tagID = itemTags.tagID
				and tags.name LIKE '%{0}%'
			""".format(query)
	tag_info = cur.execute(tag_query).fetchall()

	keys_list = []
	for item in tag_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def attachment(query):
	attachment_query = """
		select items.key
		from items, itemAttachments
		where 
			items.itemID = itemAttachments.sourceItemID
			and itemAttachments.path LIKE '%{0}%'
		""".format(query)
	attachment_info = cur.execute(attachment_query).fetchall()

	keys_list = []
	for item in attachment_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def note(query):
	notes_query = """
		select items.key
		from items, itemNotes
		where 
			items.itemID = itemNotes.sourceItemID
			and itemNotes.note LIKE '%{0}%'
	""".format(query)
	note_info = cur.execute(notes_query).fetchall()	

	keys_list = []
	for item in note_info:
		keys_list.append(item[0])
	return list(set(keys_list))


def general(query):
	nx = note(query)
	attx = attachment(query)
	tagx = tag(query)
	cx = collection(query)
	aux = author(query)
	tix = title(query)

	gen = nx + attx + tagx + cx + aux + tix

	return list(set(gen))
