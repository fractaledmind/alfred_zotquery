#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Standard Library
import re
import subprocess
# Internal Dependencies
from lib import html2text, utils
from . import zq
import setup
import search


# 1.  -------------------------------------------------------------------------
def export(flag, uid, wf):
    """Use Zotero API to export formatted references.

    :returns: format of exported text
    :rtype: ``unicode``

    """
    # Retrieve HTML of item
    cites = get_export_html(flag, uid, wf)
    # Export text of item to clipboard
    text = export_formatted(cites, flag, wf)
    utils.set_clipboard(text.strip())
    return zq.backend.output_format


# 1.1  ------------------------------------------------------------------------
def get_export_html(flag, uid, wf):
    """Get HTML of item reference.

    """
    # check if item reference has already been generated and cached
    no_cache = True
    cached = wf.cached_data(uid, max_age=600)
    if cached:
        # check if item reference is right kind
        if flag in cached.keys():
            cites = cached[flag]
            no_cache = False
    # if not exported before
    if no_cache:
        # Choose appropriate code branch
        if flag in ('bib', 'citation'):
            cites = export_item(flag, uid)
        elif flag == 'group':
            cites = export_group(uid)
        # Cache exported HTML?
        if setup.CACHE_REFERENCES:
            cache = {flag: cites}
            wf.cache_data(uid, cache)
    return cites


## 1.1.1  ---------------------------------------------------------------------
def export_item(flag, uid):
    """Export individual item in preferred format.

    """
    item_id = uid.split('_')[1]
    cite = zq.web.item(item_id,
                       include=flag,
                       style=zq.backend.csl_style)
    return cite[flag]


## 1.1.2  ---------------------------------------------------------------------
def export_group(uid):
    """Export entire group in preferred format.

    """
    group_type, item_id = uid.split('_')
    if group_type == 'c':
        marker = item_id
        ref_method = zq.web.collection_references
    elif group_type == 't':
        marker = search._get_tag_name(item_id)
        ref_method = zq.web.tag_references
    cites = ref_method(marker,
                       style=zq.backend.csl_style)
    bib = '\n\n'.join(cites)
    return _bib_sort(bib, '\n\n')


### 1.1.2.1  ------------------------------------------------------------------
def _bib_sort(bib, delim):
    """Sort multi item bibliography.

    """
    sorted_bib = sorted(bib.split(delim))
    if sorted_bib[0] == '':
        sorted_bib[0] = 'WORKS CITED'
    else:
        sorted_bib.insert(0, 'WORKS CITED')
    return delim.join(sorted_bib)


## 1.2  -----------------------------------------------------------------------
def export_formatted(cites, flag, wf):
    """Format the HTML citations in the proper format.

    """
    if zq.backend.output_format == 'Markdown':
        return _export_markdown(cites, flag)
    elif zq.backend.output_format == 'Rich Text':
        return _export_rtf(cites, flag, wf)
    else:
        msg = 'Invalid format: {}'.format(zq.backend.output_format)
        raise ValueError(msg)


#### 1.2.1  -------------------------------------------------------------------
def _export_markdown(html, flag):
    """Convert to Markdown"""
    html = _prepare_html(html)
    markdown = html2text.html2text(html, bodywidth=0)
    if flag == 'citation':
        if zq.backend.csl_style == 'bibtex':
            markdown = '[@' + markdown.strip() + ']'
    return markdown


#### 1.2.2  -------------------------------------------------------------------
def _export_rtf(html, flag, wf):
    """Convert to RTF"""
    path = wf.cachefile('temp_export.html')
    html = _prepare_html(html)
    if flag == 'citation':
        if zq.backend.csl_style == 'bibtex':
            html = '[@' + html.strip() + ']'
    utils.write_path(html, path)
    rtf = html2rtf(path)
    return rtf


##### 1.2.1.1; 1.2.2.1 --------------------------------------------------------
def _prepare_html(html):
    """Prepare HTML"""
    html = _preprocess(html)
    ascii_html = html.encode('ascii', 'xmlcharrefreplace')
    return ascii_html.strip()


##### 1.2.2.2  ----------------------------------------------------------------
def html2rtf(path):
    """Convert html to RTF and copy to clipboard"""
    return subprocess.check_output(['textutil',
                                    '-convert',
                                    'rtf',
                                    path,
                                    '-stdout'])


###### 1.2.1.1.1  -------------------------------------------------------------
def _preprocess(item):
    """Clean up `item` formatting"""
    if zq.backend.csl_style != 'bibtex':
        item = re.sub(r'(http|doi)(.*?)(?=<)', "", item)
    item = re.sub("’", "'", item)
    item = re.sub("pp. ", "", item)
    return item
