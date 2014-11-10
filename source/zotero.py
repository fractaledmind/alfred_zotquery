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
import os.path
import subprocess

# Internal Dependencies
import utils
import config
from lib import pashua
from config import PropertyBase, stored_property

# Alfred-Workflow
from workflow import Workflow, web

# create global methods from `Workflow()`
WF = Workflow()
decode = WF.decode


#------------------------------------------------------------------------------
# :class:`LocalZotero` --------------------------------------------------------
#------------------------------------------------------------------------------

class LocalZotero(PropertyBase):
    """Contains all relevant information about user's Zotero installation.

    |        Key         |                 Description                 |
    |--------------------|---------------------------------------------|
    | `original_sqlite`  | Zotero's internal sqlite database           |
    | `internal_storage` | Zotero's internal storage directory         |
    | `external_storage` | Zotero's external directory for attachments |

    Expects information to be stored in :file:`local_zotero.json`.
    If file does not exist, it creates and stores dictionary.

    """
    def __init__(self, wf):
        """Initialize the sub-class instance.

        :param wf: a new :class:`Workflow` instance.
        :type wf: ``object``

        """
        self.wf = wf
        # initialize base class, for access to `properties` dict
        PropertyBase.__init__(self, self.wf, secured=False)

    # Properties --------------------------------------------------------------

    @stored_property
    def original_sqlite(self):
        """Return path to Zotero's internal sqlite database.

        :returns: full path to file
        :rtype: ``unicode``

        """
        # Use `mdfind` to locate Zotero sqlite database
        sqlites = self.find_name('zotero.sqlite')
        if sqlites:
            for item in sqlites:
                if item.startswith('/Users'):
                    return item

    @stored_property
    def internal_storage(self):
        """Return path to Zotero's internal storage directory for attachments.

        :returns: full path to directory
        :rtype: ``unicode``

        """
        # Get path to Zotero's storage folder, adjacent to sqlite file
        zotero_dir = os.path.dirname(self.original_sqlite)
        storage_dir = os.path.join(zotero_dir, 'storage')
        if os.path.exists(storage_dir):
            return storage_dir
        else:
            # If above dir does not exist, read `prefs.js` file
            for name in ('dataDir', 'lastDataDir'):
                dir_pref = self.get_pref(name)
                if dir_pref:
                    return dir_pref

    @stored_property
    def external_storage(self):
        """Return path to Zotero's external storage directory for attachments.

        :returns: full path to directory
        :rtype: ``unicode``

        """
        # Read `prefs.js` file for info
        return self.get_pref('baseAttachmentPath')

    # Utility methods ---------------------------------------------------------

    def get_pref(self, pref):
        """Retrieve the value for ``pref`` in Zotero's preferences.

        :param pref: name of desired Zotero preference
        :type pref: ``unicode`` or ``str``
        :returns: Zotero preference value
        :rtype: ``unicode``

        """
        dirs = self.find_name('prefs.js')
        for path in dirs:
            if 'Zotero' or 'Firefox' in path:
                # Read text from file at `path`
                prefs = utils.read_path(path)
                pref_re = r'{}",\s"(.*?)"'.format(pref)
                data_dir = re.search(pref_re, prefs)
                try:
                    return data_dir.group(1)
                except AttributeError:
                    pass
        return None

    @staticmethod
    def find_name(name):
        """Use `mdfind` to locate file given its ``name``.

        :param name: full name of desired file
        :type name: ``unicode`` or ``str``
        :returns: list of paths to named file
        :rtype: :class:`list`

        """
        cmd = ['mdfind',
               'kMDItemFSName={}'.format(name),
               '-onlyin',
               '/']
        output = subprocess.check_output(cmd)
        # Convert newline delimited str into clean list
        output = [s.strip() for s in decode(output).split('\n')]
        return filter(None, output)


#------------------------------------------------------------------------------
# :class:`WebZotero` ----------------------------------------------------------
#------------------------------------------------------------------------------

class WebZotero(PropertyBase):
    """Read access to the Zotero web API (v.3)

    """
    def __init__(self, wf):
        """Store Zotero credentials."""
        self.wf = wf
        self.base = 'https://api.zotero.org'
        # save api data/properties securely
        PropertyBase.__init__(self, self.wf, secured=True)
        self.request = None
        self.links = None

    # API Properties ----------------------------------------------------------

    @stored_property
    def user_id(self):
        """User's private web API user id."""
        # If uid doesn't exist, ask for it
        # (`check_password`) is a method of :class:`PropertyBase`
        return self.check_password('user_id',
                                   self.api_properties_setter)

    @stored_property
    def api_key(self):
        """User's private web API key."""
        # If key doesn't exist, ask for it
        # (`check_password`) is a method of :class:`PropertyBase`
        return self.check_password('api_key',
                                   self.api_properties_setter)

    @stored_property
    def user_type(self):
        return 'users'
        # can also be 'groups'

    def api_properties_setter(self):
        """Ask user to input Zotero API data."""
        # Check if values have already been set
        api = self.check_password('api_key')
        uid = self.check_password('user_id')
        # Prepare `pashua` config string
        conf = """
            # Set window title
            *.title = Zotero API Settings
            # Add API Key text field
            api.type = textfield
            api.label = Enter your Zotero API Key
            api.default = {api}
            api.width = 310
            # Add User ID text field
            id.type = textfield
            id.label = Enter your Zotero User ID
            id.default = {uid}
            id.width = 310
            # Add a cancel button with default label
            cb.type=cancelbutton
        """.format(api=api, uid=uid)
        # Run `pashua` dialog and save results to Keychain
        res_dict = pashua.run(conf, encoding='utf8', pashua_path=config.PASHUA)
        if res_dict['cb'] != '1':
            self.wf.save_password('api_key', res_dict['api'])
            self.wf.save_password('user_id', res_dict['id'])

    # Basic methods -----------------------------------------------------------

    def _retrieve_data(self, request=None, **kwargs):
        """Retrieve Zotero items via the API.

        Combine endpoint and request to access the specific resource.

        Returns an JSON object

        """
        # generate URL
        full_url = '{}{}'.format(self.base, request)
        # prepare HTTP headers
        headers = {'User-Agent': "ZotQuery/{}".format(config.__version__),
                   'Authorization': "Bearer {}".format(self.api_key),
                   'Zotero-API-Version': 3}
                   #'If-Modified-Since-Version': 645}
        # ensure return format is JSON
        kwargs.update({'format': 'json'})
        # make HTTP request
        self.request = web.get(url=full_url,
                               headers=headers,
                               params=kwargs)
        # get any and all relative links from response
        self.links = self._extract_links()
        self.request.raise_for_status()
        return self.request.json()

    def _prep_url(self, url, var=None):
        """Properly format Zotero API URL."""
        if var is None:
            return url.format(t=self.user_type,
                              u=self.user_id)
        else:
            return url.format(t=self.user_type,
                              u=self.user_id,
                              x=var)

    def _extract_links(self):
        """Extract all links from Zotero API response."""
        try:
            links = self.request.headers['link']
            link_data = re.findall(r'<(.*?)>;\srel="(.*?)"', links)
            extracted = {}
            for link in link_data:
                url, key = link
                extracted[key] = url
            return extracted
        except KeyError:
            return None

    # Decorators  -------------------------------------------------------------

    def general_query(func):
        """Decorator for generic API calls."""
        def func_wrapper(self, **kwargs):
            url = self._prep_url(func(self))
            return self._retrieve_data(url, **kwargs)
        return func_wrapper

    def specific_query(func):
        """Decorator for specific API calls."""
        def func_wrapper(self, item_id, **kwargs):
            url = self._prep_url(func(self, item_id), item_id)
            return self._retrieve_data(url, **kwargs)
        return func_wrapper

    # No argument  ------------------------------------------------------------

    @general_query
    def items(self, **kwargs):
        """Get items from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/items"

    @general_query
    def top_items(self, **kwargs):
        """Get top-level items from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/items/top"

    @general_query
    def trash_items(self, **kwargs):
        """Get items in trash from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/items/trash"

    @general_query
    def tags(self, **kwargs):
        """Get tags from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/tags"

    @general_query
    def collections(self, **kwargs):
        """Get collections from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/collections"

    @general_query
    def top_collections(self, **kwargs):
        """Get top-level collections from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/collections/top"

    # Requires Argument  ------------------------------------------------------

    @specific_query
    def item(self, item_id, **kwargs):
        """Get individual item from Zotero.

        :rtype: ``dict``
        """
        return "/{t}/{u}/items/{x}"

    @specific_query
    def collection(self, collection_id, **kwargs):
        """Get individual collection from Zotero.

        :rtype: ``dict``
        """
        return "/{t}/{u}/collections/{x}"

    @specific_query
    def item_children(self, item_id, **kwargs):
        """Get all items that are children of `item_id` from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/items/{x}/children"

    @specific_query
    def item_tags(self, item_id, **kwargs):
        """Get tags of `item_id` from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/items/{x}/tags"

    @specific_query
    def tag(self, tag_name, **kwargs):
        """Get individual tag from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/tags/{x}"

    @specific_query
    def collection_children(self, coll_id, **kwargs):
        """Get all collections that are children of `coll_id` from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/collections/{x}/collections"

    @specific_query
    def collection_items(self, coll_id, **kwargs):
        """Get all items within `coll_id` from Zotero.

        :rtype: ``list``
        """
        return "/{t}/{u}/collections/{x}/items"

    #TODO: broken
    def follow(self):
        """Return the result of the call to the URL in the 'Next' link."""
        if self.links:
            url = self.links.get('next')
            return self._retrieve_data(url)
        else:
            return None

    ## ------------------------------------------------------------------------
    ## Full Reference Read API requests  --------------------------------------
    ## ------------------------------------------------------------------------

    def item_reference(self, item, **kwargs):
        info = self.item(item,
                         include='bib',
                         **kwargs)
        return info['bib']

    def tag_references(self, tag_name, **kwargs):
        info = self.items(include='bib',
                          tag=tag_name,
                          itemType='-attachment || note',
                          limit=100,
                          **kwargs)
        return [x['bib'] for x in info]

    def collection_references(self, collection, **kwargs):
        info = self.collection_items(collection,
                                     include='bib',
                                     itemType='-attachment || note',
                                     limit=100,
                                     **kwargs)
        return [x['bib'] for x in info]

    def items_references(self, item_keys, **kwargs):
        keys = ','.join(item_keys)
        info = self.items(include='bib',
                          itemKeys=keys,
                          limit=100,
                          **kwargs)
        return [x['bib'] for x in info]

    ## ------------------------------------------------------------------------
    ## Short Citation Read API requests  --------------------------------------
    ## ------------------------------------------------------------------------

    def item_citation(self, item, **kwargs):
        info = self.item(item,
                         include='citation',
                         **kwargs)
        return info['citation']

    def items_citations(self, item_keys, **kwargs):
        keys = ','.join(item_keys)
        info = self.items(include='citation',
                          itemKeys=keys,
                          limit=100,
                          **kwargs)
        return [x['citation'] for x in info]

    ## ------------------------------------------------------------------------
    ## Citation and Reference Read API requests  ------------------------------
    ## ------------------------------------------------------------------------

    def items_bibliography(self, item_keys, **kwargs):
        keys = ','.join(item_keys)
        info = self.items(include='citation,bib',
                          itemKey=keys,
                          **kwargs)
        citations = [x['citation'] for x in info]
        references = [x['bib'] for x in info]
        return {'cites': citations, 'refs': references}

#-----------------------------------------------------------------------------
# Aliases
#-----------------------------------------------------------------------------

api = WebZotero
zot = LocalZotero
