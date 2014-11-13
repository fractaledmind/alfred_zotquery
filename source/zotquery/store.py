#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Internal Dependencies
from lib import utils
import config


# 1.  ------------------------------
def store(flag, arg, wf):
    """Store data in appropriate file.

    :returns: status of store process
    :rtype: :class:`boolean`

    """
    path = wf.cachefile('{}_query_result.txt'.format(flag))
    utils.write_path(arg, path)
    config.log.info('Item ID stored in cache file.')
    return True
