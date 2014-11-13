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
import re
import sys
import sqlite3
import os.path
import subprocess

# Internal Dependencies
import config
from lib.docopt import docopt
from lib import html2text, utils
from zotero import api
from backend import data

# Alfred-Workflow
from workflow import Workflow, ICON_WARNING
from workflow.workflow import isascii

# create global methods from `Workflow()`
WF = Workflow()
log = WF.logger
decode = WF.decode
fold = WF.fold_to_ascii


#------------------------------------------------------------------------------
# :class:`ZotWorkflow` --------------------------------------------------------
#------------------------------------------------------------------------------

# TODO: break up codepaths into classes
class ZotWorkflow(object):
    """Represents all the Alfred Workflow actions.

    :param wf: a :class:`Workflow` instance.
    :type wf: :class:`object`

    """
    def __init__(self, wf):
        self.wf = wf
        self.flag = None
        self.arg = None
        # initialize data classes
        self.zotquery = data(self.wf)
        self.zotero = self.zotquery.zotero
        self.zotero_api = None

  #----------------------------------------------------------------------------
  ## Main API methods
  #----------------------------------------------------------------------------

    def run(self, args):
        """Main API method.

        :param args: command line arguments passed to workflow
        :type args: :class:`dict`
        :returns: whatever the `method` returns
        :rtype: UNKOWN (see ind. methods for info)

        """
        self.flag = args['<flag>']
        self.arg = args['<argument>']
        # list of all possible actions
        actions = ('search', 'store', 'export', 'append',
                   'open', 'config', 'scan')
        for action in actions:
            if args.get(action):
                method_name = '{}_codepath'.format(action)
                method = getattr(self, method_name, None)
                if method:
                    return method()
                else:
                    raise ValueError('Unknown action: {}'.format(action))

    # `search` paths  ---------------------------------------------------------

    def search_codepath(self):
        """Search and show data for given scope and input query.

        """
        # Search for individual items
        if self.flag in config.SCOPE_TYPES['items']:
            self.search_items()
        # Search for individual groups
        elif self.flag in config.SCOPE_TYPES['groups']:
            self.search_groups()
        # Search for individual items in an individual group
        elif self.flag in config.SCOPE_TYPES['in-groups']:
            self.search_in_groups()
        # Search for certain debugging options
        elif self.flag in config.SCOPE_TYPES['meta']:
            if self.flag == 'debug':
                self.search_debug()
            elif self.flag == 'new':
                self.search_new()
        else:
            raise ValueError('Unknown search flag: {}'.format(self.flag))
        # Return whatever feedback is generated to Alfred
        self.wf.send_feedback()

    # `store` paths  ----------------------------------------------------------

    def store_codepath(self):
        """Store data in appropriate file.

        :returns: status of store process
        :rtype: :class:`boolean`

        """
        # TODO: use `self.wf.cache_data()`
        path = self.wf.cachefile('{}_query_result.txt'.format(self.flag))
        utils.write_path(self.arg, path)
        return True

    # `export` paths  ---------------------------------------------------------

    def export_codepath(self):
        """Use Zotero API to export formatted references.

        :returns: status of export process
        :rtype: :class:`boolean`

        """
        self.zotero_api = api(self.wf)
        # Retrieve HTML of item
        cites = self.get_export_html()
        # Export text of item to clipboard
        text = self.export_formatted(cites)
        utils.set_clipboard(text.strip())
        return self.zotquery.output_format

    def append_codepath(self):
        """Use Zotero API to export formatted references.

        :returns: status of export process
        :rtype: :class:`boolean`

        """
        self.zotero_api = api(self.wf)
        # Retrieve HTML of item
        cites = self.get_export_html()
        # Append text of temp biblio
        self.append_item(cites)
        return self.zotquery.output_format

    # `open` paths  -----------------------------------------------------------

    def open_codepath(self):
        """Open item or item's attachment.

        """
        if self.flag == 'item':
            self.open_item()
        elif self.flag == 'attachment':
            self.open_attachment()

    # `config` paths  ---------------------------------------------------------

    def config_codepath(self):
        """Configure ZotQuery Workflow

        """
        if self.flag == 'freshen':
            self.config_freshen()
        elif self.flag == 'api':
            self.zotero_api = api(self.wf)
            self.zotero_api.api_properties_setter()
        elif self.flag == 'prefs':
            self.zotquery.formatting_properties_setter()
        elif self.flag == 'all':
            self.zotero_api = api(self.wf)
            self.zotero_api.api_properties_setter()
            self.zotquery.formatting_properties_setter()

    # `scan` paths ------------------------------------------------------------

    # TODO
    def scan_codepath(self):
        """Scan Markdown document for reference

        """
        if self.flag == 'temp_bib':
            return self.read_temp_bib()
        else:
            md_text = utils.read_path(self.flag)
            key_dicts = self.reference_scan(md_text)
            self.generate_bibliography(key_dicts, md_text)

    # TODO
    def generate_bibliography(self, key_dicts, md_text):
        keys = [x['key'] for x in key_dicts]
        print len(keys)
        #citekeys = [x['citekey'] for x in key_dicts]
        dict = self.zot.items_bibliography(keys, style=self.zotquery.csl_style)
        citations, references = dict['cites'], dict['refs']
        print len(citations)
        #citations, references = '\n'.join(citations), '\n'.join(references)
        #print self.export_formatted(citations)

    # TODO
    def reference_scan(self, md_text):
        """Scan Markdown document for reference

        Adapted from <https://github.com/smathot/academicmarkdown>

        """
        data = utils.read_json(self.zotquery.json_data)
        keys = data.keys()
        ref_count = 1
        zot_items = []
        found_cks = []
        # Needs to match patter created in QUICK_COPY
        regexp = re.compile(r'{@([^_]*?)_(\d*?)_([A-Z1-9]{3})}')
        for reg_obj in re.finditer(regexp, md_text):
            family, date, key_end = reg_obj.groups()
            citekey = '{@' + '_'.join([family, date, key_end]) + '}'
            if key_end in found_cks:
                continue
            ref_count += 1
            possible_keys = [key for key in keys if key.endswith(key_end)]
            if len(possible_keys) > 1:
                for key in possible_keys:
                    item = data.get(key)
                    try:
                        if item['data']['date'] == date:
                            key = key
                            break
                    except KeyError:
                        pass
            else:
                key = possible_keys[0]
            zot_items.append({'key': key, 'citekey': citekey})
            found_cks.append(key_end)
        return zot_items

  #----------------------------------------------------------------------------
  ### `Search` codepaths
  #----------------------------------------------------------------------------

    # Search debugging meta options  ------------------------------------------

    def search_debug(self):
        """Debug options Filter method.

        """
        self.wf.add_item('Root', "Open ZotQuery's Root Folder?",
                         valid=True,
                         arg='workflow:openworkflow',
                         icon='icons/n_folder.png')
        self.wf.add_item('Storage', "Open ZotQuery's Storage Folder?",
                         valid=True,
                         arg='workflow:opendata',
                         icon='icons/n_folder.png')
        self.wf.add_item('Cache', "Open ZotQuery's Cache Folder?",
                         valid=True,
                         arg='workflow:opencache',
                         icon='icons/n_folder.png')
        self.wf.add_item('Logs', "Open ZotQuery's Logs?",
                         valid=True,
                         arg='workflow:openlog',
                         icon='icons/n_folder.png')

    # -------------------------------------------------------------------------

    # Search individual `items`  ----------------------------------------------

    def search_items(self):
        """Search individual items.

        """
        # Get JSON data of user's Zotero library
        data = utils.read_json(self.zotquery.json_data)
        # Get keys of all items that match specific query
        keys = self._get_items()
        for key_rank in keys:
            # Ignore rank score in (rank, key)
            key = key_rank[-1]
            # Get JSON info for that item
            item = data.get(key, None)
            if item:
                # Prepare dictionary for Alfred
                alfred = self._prepare_item_feedback(item)
                self.wf.add_item(**alfred)

    # Search Zotero `groups`  -------------------------------------------------

    def search_groups(self):
        """Search thru Zotero groups.

        """
        # Get keys of all groups that match specific query
        groups = self._get_groups()
        for group in groups:
            # Prepare dictionary for Alfred
            alfred = self._prepare_group_feedback(group)
            self.wf.add_item(**alfred)

    # Search within Zotero `groups`  ------------------------------------------

    def search_in_groups(self):
        """Search for items within selected group.

        """
        # Get name of group stored in cache
        group = self._get_group_name()
        # Get keys of all items that match query in `group`
        keys = self._get_in_group(group)
        # Get JSON data of user's Zotero library
        data = utils.read_json(self.zotquery.json_data)
        for key in keys:
            # Ignore rank score
            key = key[-1]
            # Get JSON info for that item
            item = data.get(key, None)
            if item:
                # Prepare dictionary for Alfred
                alfred = self._prepare_item_feedback(item)
                self.wf.add_item(**alfred)

    def search_new(self):
        """Show only the newest added items.

        """
        old_data = utils.read_json(self.wf.datafile('backup.json'))
        old_keys = old_data.keys()
        current_data = utils.read_json(self.zotquery.json_data)
        current_keys = current_data.keys()
        # Get list of newly added items
        new_keys = list(set(current_keys) - set(old_keys))
        if new_keys != []:
            for key in new_keys:
                # Get JSON info for that item
                item = current_data.get(key, None)
                if item:
                    # Prepare dictionary for Alfred
                    alfred = self._prepare_item_feedback(item)
                    self.wf.add_item(**alfred)
        else:
            self.wf.add_item('No new items!',
                             'No newly added items in your Zotero library.',
                             icon='icons/n_error.png')

    ## ------------------------------------------------------------------------

    ## Get keys of individual `items`  ----------------------------------------

    def _get_items(self, arg=None):
        """Search the FTS database for query.

        :returns: all items that match query
        :rtype: :class:`list`

        """
        query = self.arg if arg is None else arg
        # Prepare proper `sqlite` query for individual items
        sql = self._make_items_query(query)
        log.info('Item sqlite query :\n\t\t\t{}'.format(sql.strip()))
        # Search against either Unicode or ASCII database
        db = self.zotquery.folded_sqlite
        if not isascii(query):
            db = self.zotquery.fts_sqlite
        log.info('Connecting to : `{}`'.format(db.split('/')[-1]))
        con = sqlite3.connect(db)
        # Prepare ranking weights (all columns equal weight)
        ranks = [1.0] * len(config.FILTERS['general'])
        with con:
            # Generate ranking function
            con.create_function('rank', 1, self.zotquery.make_rank_func(ranks))
            # Query FTS database and get result keys
            results = self._do_sqlite(con, sql)
        log.info('Number of results : {}'.format(len(results)))
        return results

    ## Get name and key of Zotero `groups`  -----------------------------------

    def _get_groups(self):
        """Get name and key for all groups that match query.

        :returns: all items that match query
        :rtype: :class:`list`

        """
        # Prepare proper `sqlite` query for Zotero groups
        sql = self._make_group_query()
        log.info('Group sqlite query: {}'.format(sql.strip()))
        db = self.zotquery.cloned_sqlite
        log.info('Connecting to: {}'.format(db))
        con = sqlite3.connect(db)
        with con:
            # Query cloned database and get result keys
            results = self._do_sqlite(con, sql)
        log.info('Number of results : {}'.format(len(results)))
        return results

    ## Get keys of `items` in Zotero `group`  ---------------------------------

    def _get_in_group(self, group):
        """Get keys for all items that match query.

        :param group: name of stored group
        :type group: :class:`unicode`
        :returns: item keys
        :rtype: :class:`list`

        """
        # Prepare proper `sqlite` query for searching in Zotero groups
        sql = self._make_in_group_query(group)
        log.info('In-Group sqlite query: {}'.format(sql.strip()))
        # Search against either Unicode or ASCII database
        if not isascii(self.arg):
            db = self.zotquery.fts_sqlite
        else:
            db = self.zotquery.folded_sqlite
        log.info('Connecting to: {}'.format(db))
        con = sqlite3.connect(db)
        with con:
            # Query FTS database and get result keys
            results = self._do_sqlite(con, sql)
        log.info('Number of results : {}'.format(len(results)))
        return results

     ## Get name of `group` in cache  ------------------------------------------

    def _get_group_name(self):
        """Get name of group from stored result.

        :returns: name of group from it's ID
        :rtype: :class:`unicode`

        """
        # get group type (`collection` vs `tag`)
        flag = self.flag.split('-')[1]
        # Read saved group info
        path = self.wf.cachefile('{}_query_result.txt'.format(flag))
        group_id = utils.read_path(path)
        # Split group type from group ID
        kind, uid = group_id.split('_')
        if kind == 'c':
            group = self._get_collection_name(uid)
        elif kind == 't':
            group = self._get_tag_name(uid)
        return group

    ### -----------------------------------------------------------------------

    ### Query maker for searching Zotero `items`  -----------------------------

    def _make_items_query(self, arg=None):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get all items' keys.

        :returns: SQLITE query string for ind. items
        :rtype: :class:`unicode`

        """
        sql = """SELECT key
            FROM zotquery
            WHERE zotquery MATCH '{}'
        """
        # Make query term fuzzy searched
        if arg is None:
            fuzzy_term = self.arg + '*'
        else:
            fuzzy_term = arg + '*'
        # if `general`, search all columns
        final = fuzzy_term
        # if scoped, search only relevant columns
        if self.flag in config.FILTERS.keys():
            # Which columns for scope?
            columns = config.FILTERS.get(self.flag)
            columns.remove('key')
            # Format `column:query`
            bits = ['{}:{}'.format(col, fuzzy_term) for col in columns]
            # Make a disjunctive query
            final = ' OR '.join(bits)
        return sql.format(final)

    ### Query maker for searching Zotero `groups`  ----------------------------

    def _make_group_query(self):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get group name and key.

        :returns: SQLITE query string for ind. groups
        :rtype: :class:`unicode`

        """
        sql = """SELECT {col}, key
                FROM {table}
                WHERE {col} LIKE '{query}'
        """
        # Make query term fuzzy searched
        fuzzy_term = '%' + self.arg + '%'
        # What column name to get `name`?
        if self.flag == 'collections':
            col = 'collectionName'
        elif self.flag == 'tags':
            col = 'name'
        return sql.format(col=col,
                          table=self.flag,
                          query=fuzzy_term)

    ### Query maker for searching in Zotero `groups`  -------------------------

    def _make_in_group_query(self, group):
        """Create the proper sqlite query given the ``flag`` and ``arg``
        to get items' keys for specified ``group``.

        :param group: name of collection or tag to search within
        :type group: :class:`unicode`
        :returns: SQLITE query string for ind. items in group
        :rtype: :class:`unicode`

        """
        sql = """SELECT key
                FROM zotquery
                WHERE zotquery MATCH '{}'
        """
        # Make query term fuzzy searched
        fuzzy_term = self.arg + '*'
        # Prepare column name from ``flag``
        flag = self.flag.split('-')[1] + 's'
        # Prepare in-column search (remove error causing `'`)
        specifier = ':'.join([flag, group.replace("'", "")])
        # Make conjunctive query
        query = ' AND '.join([fuzzy_term, specifier])
        return sql.format(query)

    ### Perform `sqlite` query (w/ error handling)  ---------------------------

    def _do_sqlite(self, con, sql):
        """Perform sqlite query.

        :param con: SQLITE connection object
        :type con: :class:`object`
        :param con: SQLITE query string
        :type con: :class:`unicode`

        """
        with con:
            cur = con.cursor()
            try:
                cur.execute(sql)
                results = cur.fetchall()
            except sqlite3.OperationalError as err:
                # If the query is invalid, show an appropriate warning and exit
                if b'malformed MATCH' in err.message:
                    self.wf.add_item('Invalid query', icon=ICON_WARNING)
                    self.wf.send_feedback()
                    return 1
                # Otherwise raise error for Workflow to catch and log
                else:
                    raise err
        return results

    #### ----------------------------------------------------------------------

    #### Get name of `collection` from `key`  ---------------------------------

    def _get_collection_name(self, key):
        """Get name of tag from `key`"""
        db = self.zotquery.cloned_sqlite
        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            sql_query = """SELECT collectionName
                FROM collections
                WHERE key = "{}" """.format(key)
            col_name = cur.execute(sql_query).fetchone()
        return col_name[0]

    #### Get name of `tag` from `key`  ----------------------------------------

    def _get_tag_name(self, key):
        """Get name of tag from `key`"""
        db = self.zotquery.cloned_sqlite
        con = sqlite3.connect(db)
        with con:
            cur = con.cursor()
            sql_query = """SELECT name
                FROM tags
                WHERE key = "{}" """.format(key)
            tag_name = cur.execute(sql_query).fetchone()
        return tag_name[0]

    #### Prepare Alfred dictionary of `item` for feedback  --------------------

    def _prepare_item_feedback(self, item):
        """Format the subtitle string for ``item``

        """
        icn_type = 'n'
        alfred = {}
        alfred['title'] = self._format_title(item)
        # Format item's subtitle
        subtitle = ' '.join([self._format_creator(item),
                             self._format_date(item)])
        if item['attachments'] != []:
            icn_type = 'att'
            subtitle = ' '.join([subtitle, 'Attachments:',
                                str(len(item['attachments']))])
        alfred['subtitle'] = subtitle
        alfred['valid'] = True
        alfred['arg'] = '_'.join([str(item['library']), str(item['key'])])
        alfred['icon'] = self._format_icon(item, icn_type)
        if LARGE_TEXT:
            alfred['largetext'] = self._format_largetext(item)
        if QUICK_COPY:
            alfred['copytext'] = self._format_quickcopy(item)
        if config.ALFRED_LEARN:
            alfred['uid'] = str(item['id'])
        return alfred

    #### Prepare Alfred dictionary of `group` for feedback  -------------------

    def _prepare_group_feedback(self, group):
        """Prepare Alfred data for groups.

        """
        name, key = group
        alfred = {}
        alfred['title'] = name
        alfred['subtitle'] = self.flag[:-1].capitalize()
        alfred['valid'] = True
        alfred['arg'] = '_'.join([self.flag[0], key])
        alfred['icon'] = "icons/n_{}.png".format(self.flag[:-1])
        if config.ALFRED_LEARN:
            alfred['uid'] = str(key)
        return alfred

    ##### ---------------------------------------------------------------------

    ##### Properly format `item`'s title  -------------------------------------

    @staticmethod
    def _format_title(item):
        """Properly format the title information for ``item``.

        """
        try:
            if not item['data']['title'][-1] in ('.', '?', '!'):
                title_final = item['data']['title'] + '.'
            else:
                title_final = item['data']['title']
        except KeyError:
            title_final = 'xxx.'
        return title_final

    ##### Properly format `item`'s creator info  ------------------------------

    @staticmethod
    def _format_creator(item):
        """Properly format the creator information for ``item``.

        """
        creator_list = []
        # Order last names by index
        for author in item['creators']:
            last = author['family']
            index = author['index']
            if author['type'] == 'editor':
                last = last + ' (ed.)'
            elif author['type'] == 'translator':
                last = last + ' (trans.)'
            creator_list.insert(index, last)
        # Format last names into string
        if len(item['creators']) == 0:
            creator_ref = 'xxx.'
        elif len(item['creators']) == 1:
            creator_ref = ''.join(creator_list)
        elif len(item['creators']) == 2:
            creator_ref = ' and '.join(creator_list)
        elif len(item['creators']) > 2:
            creator_ref = ', '.join(creator_list[:-1])
            creator_ref = creator_ref + ', and ' + creator_list[-1]
        # Format final period (`.`)
        if not creator_ref[-1] in ('.', '!', '?'):
            creator_ref = creator_ref + '.'
        return creator_ref

    ##### Properly format `item`'s date  --------------------------------------

    @staticmethod
    def _format_date(item):
        """Properly format the date information for ``item``.

        """
        try:
            return str(item['data']['date']) + '.'
        except KeyError:
            return 'xxx.'

    ##### Properly format `item`'s icon  --------------------------------------

    @staticmethod
    def _format_icon(item, icn_type):
        """Properly format the icon for ``item``.

        """
        icon = 'icons/{}_written.png'.format(icn_type)
        if item['type'] == 'journalArticle':
            icon = 'icons/{}_article.png'.format(icn_type)
        elif item['type'] == 'book':
            icon = 'icons/{}_book.png'.format(icn_type)
        elif item['type'] == 'bookSection':
            icon = 'icons/{}_chapter.png'.format(icn_type)
        elif item['type'] == 'conferencePaper':
            icon = 'icons/{}_conference.png'.format(icn_type)
        return icon

    ##### Properly format `item`'s largetext  ---------------------------------

    def _format_largetext(self, item):
        """Generate `str` to be displayed by Alfred's large text.

        """
        if isinstance(LARGE_TEXT, unicode):
            # get search map from column
            json_map = config.FILTERS_MAP.get(LARGE_TEXT, None)
            if json_map:
                # get data from `item` using search map
                largetext = self.zotquery.get_datum(item, json_map)
        elif hasattr(LARGE_TEXT, '__call__'):
            largetext = LARGE_TEXT(item)
        else:
            largetext = ''
        return largetext

    ##### Properly format `item`'s quickcopy text  ----------------------------

    def _format_quickcopy(self, item):
        """Generate `str` to be copied to clipboard by `cmd+c`.

        """
        if isinstance(QUICK_COPY, unicode):
            # get search map from column
            json_map = config.FILTERS_MAP.get(QUICK_COPY, None)
            if json_map:
                # get data from `item` using search map
                quickcopy = self.zotquery.get_datum(item, json_map)
        elif hasattr(QUICK_COPY, '__call__'):
            quickcopy = QUICK_COPY(item)
        else:
            quickcopy = ''
        return quickcopy

  #----------------------------------------------------------------------------
  ### `Export` method
  #----------------------------------------------------------------------------

    # Retrieve HTML of item  --------------------------------------------------

    def get_export_html(self):
        """Get HTML of item reference.

        """
        # check if item reference has already been generated and cached
        no_cache = True
        cached = self.wf.cached_data(self.arg, max_age=0)
        if cached:
            # check if item reference is right kind
            if self.flag in cached.keys():
                cites = cached[self.flag]
                no_cache = False
        # if not exported before
        if no_cache:
            # Choose appropriate code branch
            if self.flag in ('bib', 'citation'):
                cites = self.export_item()
            elif self.flag == 'group':
                cites = self.export_group()
            # Cache exported HTML?
            if config.CACHE_REFERENCES:
                cache = {self.flag: cites}
                self.wf.cache_data(self.arg, cache)
        return cites

    ## ------------------------------------------------------------------------

    ## Export individual `items`  ---------------------------------------------

    def export_item(self):
        """Export individual item in preferred format.

        """
        item_id = self.arg.split('_')[1]
        cite = self.zotero_api.item(item_id,
                                    include=self.flag,
                                    style=self.zotquery.csl_style)
        return cite[self.flag]

    ## Export entire `tag` or `collection`  -----------------------------------

    def export_group(self):
        """Export entire group in preferred format.

        """
        group_type, item_id = self.arg.split('_')
        if group_type == 'c':
            marker = item_id
            ref_method = self.zotero_api.collection_references
        elif group_type == 't':
            marker = self._get_tag_name(item_id)
            ref_method = self.zotero_api.tag_references
        cites = ref_method(marker,
                           style=self.zotquery.csl_style)
        bib = '\n\n'.join(cites)
        return self._bib_sort(bib, '\n\n')

    ### -----------------------------------------------------------------------

    ### Append `item` to temporary bibliography  ------------------------------

    def append_item(self, cites):
        """Append citation to appropriate bibliography file.

        """
        text = self._prepare_html(cites)
        utils.append_path(text, self.wf.cachefile('temp_bibliography.html'))

    def read_temp_bib(self):
        """Read content of temporary bibliography.

        """
        path = self.wf.cachefile('temp_bibliography.html')
        bib = utils.read_path(path)
        text = self.export_formatted(bib)
        bib = self._bib_sort(text, '\n\n')
        utils.set_clipboard(bib)
        return self.zotquery.output_format

    @staticmethod
    def _bib_sort(bib, delim):
        """Sort multi item bibliography.

        """
        sorted_bib = sorted(bib.split(delim))
        if sorted_bib[0] == '':
            sorted_bib[0] = 'WORKS CITED'
        else:
            sorted_bib.insert(0, 'WORKS CITED')
        return delim.join(sorted_bib)

    ### Export properly formatted text  ---------------------------------------

    def export_formatted(self, cites):
        """Format the HTML citations in the proper format.

        """
        if self.zotquery.output_format == 'Markdown':
            final = self._export_markdown(cites)
        elif self.zotquery.output_format == 'Rich Text':
            final = self._export_rtf(cites)
        else:
            msg = 'Invalid format: {}'.format(self.zotquery.output_format)
            raise ValueError(msg)
        return final

    #### ----------------------------------------------------------------------

    #### Export text as Markdown  ---------------------------------------------

    def _export_markdown(self, html):
        """Convert to Markdown

        """
        html = self._prepare_html(html)
        markdown = html2text.html2text(html, bodywidth=0)
        if self.flag == 'citation':
            if self.zotquery.csl_style == 'bibtex':
                markdown = '[@' + markdown.strip() + ']'
        return markdown

    #### Export text as Rich Text  --------------------------------------------

    def _export_rtf(self, html):
        """Convert to RTF

        """
        path = self.wf.cachefile('temp_export.html')
        html = self._prepare_html(html)
        if self.flag == 'citation':
            if self.zotquery.csl_style == 'bibtex':
                html = '[@' + html.strip() + ']'
        utils.write_path(html, path)
        rtf = self.html2rtf(path)
        return rtf

    ##### ---------------------------------------------------------------------

    ##### Clean up and stringify HTML  ----------------------------------------

    def _prepare_html(self, html):
        """Prepare HTML

        """
        html = self._preprocess(html)
        ascii_html = html.encode('ascii', 'xmlcharrefreplace')
        return ascii_html.strip()

    ##### Convert HTML to Rich Text  ------------------------------------------

    @staticmethod
    def html2rtf(path):
        """Convert html to RTF and copy to clipboard"""
        return subprocess.check_output(['textutil',
                                        '-convert',
                                        'rtf',
                                        path,
                                        '-stdout'])

    ##### Clean up odd formatting  --------------------------------------------

    def _preprocess(self, item):
        """Clean up `item` formatting"""
        if self.zotquery.csl_style != 'bibtex':
            item = re.sub(r'(http|doi)(.*?)(?=<)', "", item)
        item = re.sub("’", "'", item)
        item = re.sub("pp. ", "", item)
        return item

  #----------------------------------------------------------------------------
  ### `Open` method
  #----------------------------------------------------------------------------

    # Open individual `items`  ------------------------------------------------

    def open_item(self):
        """Open item in Zotero client"""
        if self.zotquery.zotero_app == 'Standalone':
            app_id = 'org.zotero.zotero'
        elif self.zotquery.zotero_app == 'Firefox':
            app_id = 'org.mozilla.firefox'
        else:
            msg = 'Invalid app name: {}'.format(self.zotquery.zotero_app)
            raise ValueError(msg)

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
            """.format(self.arg, app_id)
        return utils.run_applescript(scpt_str)

    # Open `item`'s attachment  -----------------------------------------------

    def open_attachment(self):
        """Open item's attachment in default app"""
        if os.path.isfile(self.arg):
            subprocess.check_output(['open', self.arg])
        # if self.input is item key
        else:
            data = utils.read_json(self.zotquery.json_data)
            item_id = self.arg.split('_')[1]
            item = data.get(item_id, None)
            if item:
                for att in item['attachments']:
                    if os.path.exists(att['path']):
                        subprocess.check_output(['open', att['path']])

  #----------------------------------------------------------------------------
  ### `Config` codepaths
  #----------------------------------------------------------------------------

    def config_freshen(self):
        """Update relevant data stores.

        """
        if self.arg == 'True':
            self.zotquery.update_clone()
            self.zotquery.update_json()
            return 0
        update, spot = self.zotquery.is_fresh()
        if update:
            if spot == 'Clone':
                self.zotquery.update_clone()
            elif spot == 'JSON':
                self.zotquery.update_json()
        return 0


#-----------------------------------------------------------------------------
# Main Script
#-----------------------------------------------------------------------------

def main(wf):
    """Accept Alfred's args and pipe to workflow class"""
    argv = docopt(config.__usage__,
                  argv=wf.args,
                  version=config.__version__)
    log.info(wf.args)
    pd = ZotWorkflow(wf)
    res = pd.run(argv)
    if res:
        print(res)

if __name__ == '__main__':
    sys.exit(WF.run(main))
