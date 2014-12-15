#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Internal Dependencies
from lib import utils
from . import zq
import setup
import export


# 1.  ------------------------------
def append(flag, arg, wf):
    """Use Zotero API to export formatted references.

    :returns: status of export process
    :rtype: :class:`boolean`

    """
    # Retrieve HTML of item
    cites = export.get_export_html(flag, arg, wf)
    # Append text of temp biblio
    append_item(cites, wf)
    return zq.backend.output_format


## 1.1  -------------------------
def append_item(cites, wf):
    """Append citation to appropriate bibliography file.

    """
    text = export._prepare_html(cites)
    utils.append_path(text, wf.cachefile('temp_bibliography.html'))
    setup.log.info('HTML appended to temporary bibliography.')
    return True
