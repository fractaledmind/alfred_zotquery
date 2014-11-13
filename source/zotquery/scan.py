#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import re
# Internal Dependencies
from lib import utils
from . import zq
import export


# 1.  ------------------------------
def scan(flag, arg, wf):
    """Scan Markdown document for reference

    """
    if flag == 'temp_bib':
        return read_temp_bib(wf)
    else:
        md_text = utils.read_path(flag)
        key_dicts = reference_scan(md_text)
        generate_bibliography(key_dicts, md_text)


# TODO
def generate_bibliography(key_dicts, md_text):
    keys = [x['key'] for x in key_dicts]
    print len(keys)
    #citekeys = [x['citekey'] for x in key_dicts]
    dict = zq.web.items_bibliography(keys,
                                     style=zq.backend.csl_style)
    citations, references = dict['cites'], dict['refs']
    print len(citations)
    #citations, references = '\n'.join(citations), '\n'.join(references)
    #print export_formatted(citations)


# TODO
def reference_scan(md_text):
    """Scan Markdown document for reference

    Adapted from <https://github.com/smathot/academicmarkdown>

    """
    data = utils.read_json(zq.backend.json_data)
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


def read_temp_bib(wf):
    """Read content of temporary bibliography.

    """
    path = wf.cachefile('temp_bibliography.html')
    bib = utils.read_path(path)
    text = export.export_formatted(bib)
    bib = export._bib_sort(text, '\n\n')
    utils.set_clipboard(bib)
    return zq.backend.output_format
