#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Standard Library
import sqlite3
# Internal Dependencies
from workflow.workflow import isascii
from lib import utils
from . import zq
import setup


#------------------------------------------------------------------------------
#  Class to convert ZotQuery dictionaries into Alfred dictionaries
#------------------------------------------------------------------------------

class ResultsFormatter(object):
    """Convert ZotQuery Python ``dict`` into Alfred results ``dict``.

    For example, this class will convert the following ZotQuery dictionary:
        ```
        "MNMJCJ4T": {
          "key": "MNMJCJ4T",
          "library": "0",
          "type": "book",
          "creators": [
            {
              "index": 1,
              "given": "Kirk R.",
              "type": "editor",
              "family": "Sanders"
            },
            {
              "index": 0,
              "given": "Jeffrey",
              "type": "editor",
              "family": "Fish"
            }
          ],
          "data": {
            "publisher": "Cambridge University Press",
            "ISBN": "0521194784",
            "date": "2011",
            "extra": "Cited by 0001",
            "libraryCatalog": "Amazon.com",
            "title": "Epicurus and the Epicurean Tradition",
            "numPages": 280
          },
          "zot-collections": [
            {
              "library_id": "0",
              "group": "personal",
              "name": "Epicurus on Friendship",
              "key": "GXWGBRJD"
            },
            {
              "library_id": "0",
              "group": "personal",
              "name": "Sources",
              "key": "WU57N494"
            }
          ],
          "zot-tags": [],
          "attachments": [
            {
              "path": "/Users/smargh/Downloads/fish_sanders_2011_epicurus and the epicurean tradition_book.pdf",
              "name": "fish_sanders_2011_epicurus and the epicurean tradition_book.pdf",
              "key": "T2E9X482"
            }
          ],
          "notes": []
        }
        ```

    This item would be converted into the following Alfred-ready dictionary:
        ```
        {
            "largetext": "",
            "subtitle": "Fish (ed.) and Sanders (ed.). 2011. Attachments: 1",
            "title": "Epicurus and the Epicurean Tradition.",
            "valid": true,
            "arg": "0_MNMJCJ4T",
            "copytext": "{@Sanders, & Fish_2011_J4T}",
            "icon": "icons/att_book.png"
        }
        ```

    """
    def __init__(self, item):
        """``item`` is a Python dictionary for an item in the JSON db
        `zotquery.json`.

        """
        self.item = item

    def prepare_item_feedback(self):
        """Format the subtitle string for ``item``

        """
        alfred = {}
        alfred['title'] = self.format_title()
        alfred['subtitle'] = self.format_subtitle()
        alfred['valid'] = True
        alfred['arg'] = self.format_arg()
        alfred['icon'] = self.format_icon()
        alfred['largetext'] = self.format_largetext()
        alfred['copytext'] = self.format_quickcopy()
        if setup.ALFRED_LEARN:
            alfred['uid'] = str(self.item['id'])
        return alfred

    def prepare_group_feedback(self):
        """Prepare Alfred data for groups.

        """
        #{'flag': scope, 'name': coll[0], 'key': coll[1]}
        alfred = {}
        alfred['title'] = self.item['name']
        alfred['subtitle'] = self.item['flag'][:-1].capitalize()
        alfred['valid'] = True
        alfred['arg'] = '_'.join([self.item['flag'][0], self.item['key']])
        alfred['icon'] = "icons/n_{}.png".format(self.item['flag'][:-1])
        if setup.ALFRED_LEARN:
            alfred['uid'] = str(self.item['key'])
        return alfred

    ##  -----------------------------------------------------------------------

    def format_title(self):
        """Properly format the title information for ``item``.

        """
        try:
            if not self.item['data']['title'][-1] in ('.', '?', '!'):
                title_final = self.item['data']['title'] + '.'
            else:
                title_final = self.item['data']['title']
        except KeyError:
            title_final = 'xxx.'
        return title_final

    def format_subtitle(self):
        subtitle = ' '.join([self.format_creator(),
                             self.format_date()])
        if self.item['attachments'] != []:
            subtitle = ' '.join([subtitle, 'Attachments:',
                                str(len(self.item['attachments']))])
        return subtitle

    def format_arg(self):
        return '_'.join([str(self.item['library']),
                         str(self.item['key'])])

    def format_icon(self):
        """Properly format the icon for ``item``.

        """
        icn_type = 'n'
        if self.item['attachments'] != []:
            icn_type = 'att'

        icon = 'icons/{}_written.png'.format(icn_type)
        if self.item['type'] == 'journalArticle':
            icon = 'icons/{}_article.png'.format(icn_type)
        elif self.item['type'] == 'book':
            icon = 'icons/{}_book.png'.format(icn_type)
        elif self.item['type'] == 'bookSection':
            icon = 'icons/{}_chapter.png'.format(icn_type)
        elif self.item['type'] == 'conferencePaper':
            icon = 'icons/{}_conference.png'.format(icn_type)
        return icon

    def format_largetext(self):
        """Generate `str` to be displayed by Alfred's large text.

        """
        if isinstance(setup.LARGE_TEXT, unicode):
            # get search map from column
            json_map = setup.FILTERS_MAP.get(setup.LARGE_TEXT, None)
            if json_map:
                # get data from `item` using search map
                largetext = zq.backend.get_datum(self.item, json_map)
        elif hasattr(setup.LARGE_TEXT, '__call__'):
            largetext = setup.LARGE_TEXT(self.item)
        else:
            largetext = ''
        return largetext

    def format_quickcopy(self):
        """Generate `str` to be copied to clipboard by `cmd+c`.

        """
        if isinstance(setup.QUICK_COPY, unicode):
            # get search map from column
            json_map = setup.FILTERS_MAP.get(setup.QUICK_COPY, None)
            if json_map:
                # get data from `item` using search map
                quickcopy = zq.backend.get_datum(self.item, json_map)
        elif hasattr(setup.QUICK_COPY, '__call__'):
            quickcopy = setup.QUICK_COPY(self.item)
        else:
            quickcopy = ''
        return quickcopy

    ###  ----------------------------------------------------------------------

    def format_creator(self):
        """Properly format the creator information for ``item``.

        """
        creators_num = len(self.item['creators'])
        creator_list = []
        # Order last names by index
        for author in self.item['creators']:
            index = author['index']
            if author['family']:
                last = author['family']
            else:
                last = 'xxx.'
            if author['type'] == 'editor':
                last = last + ' (ed.)'
            elif author['type'] == 'translator':
                last = last + ' (trans.)'
            creator_list.insert(index, last)
        # Format last names into string
        if creators_num == 0:
            creator_ref = 'xxx.'
        elif creators_num == 1:
            creator_ref = ''.join(creator_list)
        elif creators_num == 2:
            creator_ref = ' and '.join(creator_list)
        elif creators_num > 2:
            creator_ref = ', '.join(creator_list[:-1])
            creator_ref = creator_ref + ', and ' + creator_list[-1]
        # Format final period (`.`)
        if not creator_ref[-1] in ('.', '!', '?'):
            creator_ref = creator_ref + '.'
        return creator_ref

    def format_date(self):
        """Properly format the date information for ``item``.

        """
        try:
            return str(self.item['data']['date']) + '.'
        except KeyError:
            return 'xxx.'


#------------------------------------------------------------------------------
#  Functions to search for individual items
#------------------------------------------------------------------------------

# 1.  -------------------------------------------------------------------------
def search_for_items(scope, query):
    # Generate appropriate sqlite query
    sqlite_query = make_item_sqlite_query(scope, query)
    setup.log.info('Item sqlite query : {}'.format(sqlite_query))
    # Run sqlite query and get back item keys
    item_keys = run_item_sqlite_query(sqlite_query)
    # Get JSON data of user's Zotero library
    data = utils.read_json(zq.backend.json_data)
    results_dict = []
    for key in item_keys:
        item = data.get(key, None)
        if item:
            # Prepare dictionary for Alfred
            formatter = ResultsFormatter(item)
            alfred_dict = formatter.prepare_item_feedback()
            results_dict.append(alfred_dict)
    return results_dict


## 1.1  -----------------------------------------------------------------------
def make_item_sqlite_query(scope, query):
    fuzzy_query = make_item_fuzzy(query)
    columns = get_item_columns(scope)
    query = make_disjunctive_item_query(fuzzy_query, columns)
    return get_item_sql().format(query)


### 1.1.1  --------------------------------------------------------------------
def make_item_fuzzy(query):
    return ''.join([query, '*'])


### 1.1.2  --------------------------------------------------------------------
def get_item_columns(scope):
    if scope in setup.FILTERS.keys():
        columns = setup.FILTERS.get(scope)
        columns.remove('key')
        return columns
    else:
        msg = 'Invalid search scope : `{}`'.format(scope)
        raise Exception(msg)


### 1.1.3  --------------------------------------------------------------------
def make_disjunctive_item_query(query, columns):
    # Format `column:query`
    bits = ['{}:{}'.format(col, query)
            for col in columns]
    # Make a disjunctive query
    return ' OR '.join(bits)


### 1.1.4; 3.2.2.1  -----------------------------------------------------------
def get_item_sql():
    sections = ("SELECT key, rank(matchinfo(zotquery)) AS score",
                "FROM zotquery",
                "WHERE zotquery MATCH '{}'",
                "ORDER BY score DESC;")
    sql_str = ' '.join(sections)
    return sql_str.strip()


## 1.2  -----------------------------------------------------------------------
def run_item_sqlite_query(query):
    db = get_fts_db(query)
    setup.log.info('Connecting to : `{}`'.format(db.split('/')[-1]))

    def ranker(con):
        ranks = [1.0] * len(setup.FILTERS['general'])
        con.create_function('rank',
                            1,
                            zq.backend.make_rank_func(ranks))

    results = execute_sql(db, query, context=ranker).fetchall()
    setup.log.info('Number of results : {}'.format(len(results)))
    # Omit rankings from the returned list
    return [x[0] for x in results]


### 1.2.1  --------------------------------------------------------------------
def get_fts_db(query):
    # Search against either Unicode or ASCII database
    db = zq.backend.folded_sqlite
    if not isascii(query):
        db = zq.backend.fts_sqlite
    return db


## 1.3  -----------------------------------------------------------------------
def get_item_dict(key):
    item = data.get(key, None)


#------------------------------------------------------------------------------
#  Functions to search *for* groups
#------------------------------------------------------------------------------

# 2.  -------------------------------------------------------------------------
def search_for_groups(scope, query):
    # Generate appropriate sqlite query
    sqlite_query = make_group_sqlite_query(scope, query)
    setup.log.info('Item sqlite query : {}'.format(sqlite_query))
    # Run sqlite query and get back item keys
    coll_data = run_group_sqlite_query(sqlite_query)
    coll_dicts = [{'flag': scope, 'name': coll[0], 'key': coll[1]}
                  for coll in coll_data]
    results_dict = []
    for coll in coll_dicts:
        # Prepare dictionary for Alfred
        formatter = ResultsFormatter(coll)
        alfred_dict = formatter.prepare_group_feedback()
        results_dict.append(alfred_dict)
    return results_dict


## 2.1  -----------------------------------------------------------------------
def make_group_sqlite_query(scope, query):
    fuzzy_query = make_group_fuzzy(query)
    column = get_group_column(scope)
    return get_group_sql().format(col=column,
                                  table=scope,
                                  query=fuzzy_query)


### 2.1.1  --------------------------------------------------------------------
def make_group_fuzzy(query):
    return ''.join([query, '%'])


### 2.1.2  --------------------------------------------------------------------
def get_group_column(scope):
    if scope == 'collections':
        return 'collectionName'
    elif scope == 'tags':
        return 'name'
    else:
        raise Exception('Invalid group : `{}`'.format(scope))


### 2.1.3  --------------------------------------------------------------------
def get_group_sql():
    sections = ("SELECT {col}, key",
                "FROM {table}",
                "WHERE {col} LIKE '{query}'")
    sql_str = ' '.join(sections)
    return sql_str.strip()


## 2.2  -----------------------------------------------------------------------
def run_group_sqlite_query(query):
    db = zq.backend.cloned_sqlite
    setup.log.info('Connecting to : `{}`'.format(db.split('/')[-1]))
    results = execute_sql(db, query).fetchall()
    setup.log.info('Number of results : {}'.format(len(results)))
    return results


#------------------------------------------------------------------------------
#  Functions to search *within* groups
#------------------------------------------------------------------------------

# 3.  -------------------------------------------------------------------------
def search_within_group(scope, query):
    group_type = scope.split('-')[-1]
    # Read saved group info
    path = setup.WF.cachefile('{}_query_result.txt'.format(group_type))
    group_id = utils.read_path(path)
    group_name = get_group_name(group_id)
    sqlite_query = make_in_group_sqlite_query(scope, query, group_name)
    setup.log.info('Item sqlite query : {}'.format(sqlite_query))
    # Run sqlite query and get back item keys
    item_keys = run_item_sqlite_query(sqlite_query)
    # Get JSON data of user's Zotero library
    data = utils.read_json(zq.backend.json_data)
    results_dict = []
    for key in item_keys:
        item = data.get(key, None)
        if item:
            # Prepare dictionary for Alfred
            formatter = ResultsFormatter(item)
            alfred_dict = formatter.prepare_item_feedback()
            results_dict.append(alfred_dict)
    return results_dict


## 3.1  -----------------------------------------------------------------------
def get_group_name(group_arg):
    # Split group type from group ID
    kind, uid = group_arg.split('_')
    if kind == 'c':
        return get_collection_name(uid)
    elif kind == 't':
        return get_tag_name(uid)
    else:
        raise Exception('Invalid group id : `{}`'.format(group_arg))


### 3.1.1  --------------------------------------------------------------------
def get_collection_name(uid):
    """Get name of tag from `key`"""
    db = zq.backend.cloned_sqlite
    setup.log.info('Connecting to : `{}`'.format(db.split('/')[-1]))
    sql_query = """SELECT collectionName
                   FROM collections
                   WHERE key = "{}" """.format(uid)
    col_name = execute_sql(db, sql_query).fetchone()
    return col_name[0]


### 3.1.2  --------------------------------------------------------------------
def get_tag_name(uid):
    db = zq.backend.cloned_sqlite
    setup.log.info('Connecting to : `{}`'.format(db.split('/')[-1]))
    sql_query = """SELECT name
                   FROM tags
                   WHERE key = "{}" """.format(uid)
    tag_name = execute_sql(db, sql_query).fetchone()
    return tag_name[0]


#### 3.1.1.1; 2.2.1; 1.2.1  ---------------------------------------------------
def execute_sql(db, sql, context=None):
    """Execute sqlite query and return sqlite object.

    :param sql: SQL or SQLITE query string
    :type sql: :class:`unicode`
    :returns: SQLITE object of executed query
    :rtype: :class:`object`

    """
    con = sqlite3.connect(db)
    with con:
        cur = con.cursor()
        if context:
            context(con)
        try:
            return cur.execute(sql)
        except sqlite3.OperationalError as err:
            # If the query is invalid,
            # show an appropriate warning and exit
            if b'malformed MATCH' in err.message:
                setup.WF.add_item('Invalid query')
                setup.WF.send_feedback()
                return 1
            # Otherwise raise error for Workflow to catch and log
            else:
                raise err


## 3.2  -----------------------------------------------------------------------
def make_in_group_sqlite_query(scope, query, group):
    fuzzy_query = make_item_fuzzy(query)
    column = get_in_group_column(scope)
    query = make_conjunctive_item_query(fuzzy_query, column, group)
    return get_item_sql().format(query)


### 3.2.1  --------------------------------------------------------------------
def get_in_group_column(scope):
    return scope.split('-')[-1] + 's'


### 3.2.2  --------------------------------------------------------------------
def make_conjunctive_item_query(query, column, group):
    # Prepare in-column search (remove error causing `'`)
    specifier = ':'.join([column, group.replace("'", "")])
    # Make conjunctive query
    query = ' AND '.join([query, specifier])
    return query


#------------------------------------------------------------------------------
#  API
#------------------------------------------------------------------------------
def search(scope, query, wf):
    # Ensure inputs are Unicode
    scope = setup.decode(scope)
    query = setup.decode(query)
    # Search for individual items
    if scope in setup.SCOPE_TYPES['items']:
        found_items = search_for_items(scope, query)
    # Search for individual groups
    elif scope in setup.SCOPE_TYPES['groups']:
        found_items = search_for_groups(scope, query)
    # Search for individual items in an individual group
    elif scope in setup.SCOPE_TYPES['in-groups']:
        found_items = search_within_group(scope, query)
    # Search for certain debugging options
    elif scope in setup.SCOPE_TYPES['meta']:
        if scope == 'debug':
            #search_debug()
            pass
        elif scope == 'new':
            #search_new()
            pass
    else:
        raise Exception('Unknown search flag: `{}`'.format(scope))

    [wf.add_item(**item) for item in found_items]
    wf.send_feedback()
