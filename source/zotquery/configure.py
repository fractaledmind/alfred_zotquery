#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Internal Dependencies
from . import zq


# 1.  ------------------------------
def configure(flag, arg, wf):
    """Configure ZotQuery Workflow

    """
    if flag == 'freshen':
        return config_freshen(arg)
    elif flag == 'api':
        return zq.web.api_properties_setter()
    elif flag == 'prefs':
        return zq.backend.formatting_properties_setter()
    elif flag == 'all':
        return zq.web.api_properties_setter()
        return zq.backend.formatting_properties_setter()


def config_freshen(arg):
    """Update relevant data stores.

    """
    if arg == 'True':
        zq.backend.update_clone()
        zq.backend.update_json()
        return 0
    update, spot = zq.backend.is_fresh()
    if update:
        if spot == 'Clone':
            zq.backend.update_clone()
        elif spot == 'JSON':
            zq.backend.update_json()
    return 0
