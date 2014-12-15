#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import re
import os.path
import subprocess

from utils import store_properties, stored_property


@store_properties
class ZoteroPaths(object):
    """Contains all relevant information about user's Zotero installation.

    |        Key         |                 Description                 |
    |--------------------|---------------------------------------------|
    | `original_sqlite`  | Zotero's internal sqlite database           |
    | `internal_storage` | Zotero's internal storage directory         |
    | `external_storage` | Zotero's external directory for attachments |

    Expects information to be stored in :file:`local_zotero.json`.
    If file does not exist, it creates and stores dictionary.

    """
    def __init__(self):
        pass

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
                with open(path, 'r') as f:
                    prefs = f.read()
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




