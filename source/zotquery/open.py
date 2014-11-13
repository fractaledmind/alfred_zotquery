#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
# Standard Library
import os.path
import subprocess
# Internal Dependencies
from lib import utils
from . import zq


# 1.  ------------------------------
def open(flag, arg, wf):
    """Open item or item's attachment.

    """
    if flag == 'item':
        open_item(arg)
    elif flag == 'attachment':
        open_attachment(arg)


## 1.1  ------------------------------------------------
def open_item(arg):
    """Open item in Zotero client"""
    if zq.backend.zotero_app == 'Standalone':
        app_id = 'org.zotero.zotero'
    elif zq.backend.zotero_app == 'Firefox':
        app_id = 'org.mozilla.firefox'
    else:
        msg = 'Invalid app name: {}'.format(zq.backend.zotero_app)
        raise ValueError(msg)

    scpt_str = """
        set appName to name of application id "{app}"
        set startIt to false
        tell application "System Events"
            if not (exists process appName) then
                set startIt to true
            end if
        end tell
        if startIt then
            tell application appName
                open location "zotero://select/items/" & "{id}"
                set window_ids to id of every window whose id is not equal to -1
                if window_ids is not equal to {{}} then
                    my set_frontmost("Zotero")
                    open location "zotero://select/items/" & "{id}"
                else
                    activate
                    my set_frontmost("Zotero")
                    delay 1
                    open location "zotero://select/items/" & "{id}"
                    delay 0.5
                    open location "zotero://select/items/" & "{id}"
                end if
            end tell
        else
            set_frontmost(appName)
            tell application appName to open location "zotero://select/items/" & "{id}"
        end if
        on set_frontmost(app_name)
            tell application "System Events"
                repeat while frontmost of process app_name is false
                    set frontmost of process app_name to true
                end repeat
            end tell
        end set_frontmost
        """.format(id=arg, app=app_id)
    return utils.run_applescript(scpt_str)


## 1.2  -----------------------------------------------
def open_attachment(arg):
    """Open item's attachment in default app"""
    if os.path.isfile(arg):
        subprocess.check_output(['open', arg])
    # if self.input is item key
    else:
        data = utils.read_json(zq.backend.json_data)
        item_id = arg.split('_')[-1]
        item = data.get(item_id, None)
        if item:
            for att in item['attachments']:
                if os.path.exists(att['path']):
                    subprocess.check_output(['open', att['path']])
