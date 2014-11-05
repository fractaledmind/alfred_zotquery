#!/usr/bin/python
# encoding: utf-8
import sys
import sqlite3
import os.path
import struct
from time import time
import zot_helpers as zot
from workflow import Workflow, ICON_INFO, ICON_WARNING


def get_datum(item, val_map):
    """Retrieve content of ``val_map`` from ``item``.
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
    try:
        return ' '.join(result)
    except:
        print val_map, result
        return ""

# Search ranking function
# Adapted from http://goo.gl/4QXj25 and http://goo.gl/fWg25i
def make_rank_func(weights):
    """`weights` is a list or tuple of the relative ranking per column.

    Use floats (1.0 not 1) for more accurate results. Use 0 to ignore a
    column.
    """
    def rank(matchinfo):
        # matchinfo is defined as returning 32-bit unsigned integers
        # in machine byte order
        # http://www.sqlite.org/fts3.html#matchinfo
        # and struct defaults to machine byte order
        bufsize = len(matchinfo)  # Length in bytes.
        matchinfo = [struct.unpack(b'I', matchinfo[i:i+4])[0]
                     for i in range(0, bufsize, 4)]
        it = iter(matchinfo[2:])
        return sum(x[0]*w/x[1]
                   for x, w in zip(zip(it, it, it), weights)
                   if x[1])
    return rank


class ZotIndex(object):
    """Object for sqlite's full-text search functionality.
    """
    def __init__(self, wf, scope, db=None):
        self.wf = wf
        self.scope = scope
        self.db = self.wf.datafile('zot_index.db') if db == None else db
        self.filters = zot.json_read(wf.workflowfile('index_filters.json'))
        self.scopes = self.filters.keys()
  
    def columns(self, scope):
        """Return names for all columns for the search scope table.
        """
        if scope in self.scopes:
            columns = self.filters[scope].keys()
            return columns
        else:
            raise RuntimeError('Not valid search scope: {}'.format(scope))

    def generate_data(self, scope):
        """Create a genererator with dicts for each item.
        """
        for item in zot.json_read(self.wf.datafile('zotero_db.json')):
            dict_array = []
            the_scope = self.filters.get(scope, None)
            if the_scope:
                columns = the_scope.keys()
                for column in columns:
                    json_map = the_scope.get(column, None)
                    if json_map:
                        dict_array.append({column: get_datum(item, json_map)})
            yield dict_array

    def create_index_db(self):
        """Create a "virtual" table, 
        which sqlite3 uses for its full-text search.
        """
        if not os.path.exists(self.db):
            con = sqlite3.connect(self.db)
            with con:
                cur = con.cursor()
                for scope in self.scopes:
                    columns = ', '.join(self.columns(scope))
                    sql = """CREATE VIRTUAL TABLE zot_{table}
                             USING fts3({columns})""".format(table=scope,
                                                             columns=columns)
                    cur.execute(sql)

    def update_index_db(self):
        """Read in the data source and add it to the search index database"""
        start = time()
        con = sqlite3.connect(self.db)
        count = 0
        with con:
            cur = con.cursor()
            for scope in self.scopes:
                for row in self.generate_data(scope):
                    columns = ', '.join([x.keys()[0] for x in row])
                    values = ['"' + x.values()[0].replace('"', "'") + '"'
                                for x in row]
                    values = ', '.join(values).encode('utf-8')
                    sql = """INSERT OR IGNORE INTO zot_{table}
                             ({columns}) VALUES ({data})""".format(table=scope,
                                                             columns=columns,
                                                             data=values)
                    try:
                        cur.execute(sql)
                        count += 1
                    except sqlite3.OperationalError:
                        print sql
                        return 0
        print '{} items added/updated in {:0.3} seconds'.format(
                 count, time() - start)

    def search_index_db(self):
        """N"""
        columns_list = self.columns(self.scope)

        sql = """SELECT * FROM
                    (SELECT rank(matchinfo(zot_{table}))
                    AS r, key
                    FROM zot_{table} 
                    WHERE creators MATCH '{query}')
                ORDER BY r DESC LIMIT 100
                """.format(table=self.scope,
                            query="rudd")
        con = sqlite3.connect(self.db)
        ranks = [1.0] * len(columns_list)
        with con:
            con.create_function('rank', 1, make_rank_func(tuple(ranks)))
            cur = con.cursor()
            try:
                cur.execute(sql)
                results = cur.fetchall()
            except sqlite3.OperationalError as err:
                # If the query is invalid, show an appropriate warning and exit
                if b'malformed MATCH' in err.message:
                    self.wf.add_item('Invalid query', icon=ICON_WARNING)
                    self.wf.send_feedback()
                    return
                # Otherwise raise error for Workflow to catch and log
                else:
                    raise err
        return results
        


def main(wf):
    
    zi = ZotIndex(wf, 'general')
    #zi.create_index_db()
    #zi.update_index_db()
    print zi.search_index_db()


     
    




if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
