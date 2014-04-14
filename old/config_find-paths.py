#!/usr/bin/python
# encoding: utf-8
import sys
sys.path.insert(0, 'alfred-workflow.zip')
import workflow
import os


def main(wf):
    import re
    import json
    from zq_utils import get_profile
    import applescript


    # Check to see if already configured
    if not os.path.exists(wf.datafile("paths.json")):

        # Path to apps
        _zs = os.environ["HOME"] + '/Library/Application Support/Zotero/'
        _zf = os.environ["HOME"] + '/Library/Application Support/Firefox/'

        # Profile paths
        zs_path = get_profile(_zs)
        zf_path = get_profile(_zf)

        # Path to preferences files
        zs_pref_path = zs_path + '/prefs.js'
        zf_pref_path = zf_path + '/prefs.js'

        # Regexs
        last_data_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.lastDataDir\",\s\"(.*?)\"\);")
        data_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.dataDir\",\s\"(.*?)\"\);")
        base_dir_re = re.compile(r"user_pref\(\"extensions\.zotero\.baseAttachmentPath\",\s\"(.*?)\"\);")

        
        def get_paths(prefs):
            """Search prefs.js file for Firefox or Standalone for all data"""
            
            with open(prefs, 'r') as f:
                _prefs = f.read()
                f.close()
            # Get path to data directory
            data_dir = re.search(last_data_dir_re, _prefs)
            try:
                data_path = data_dir.group(1)
            except:
                try:
                    data_dir = re.search(data_dir_re, _prefs)
                    data_path = data_dir.group(1)
                except:
                    data_path = None

            # Get path to directory for linked attachments
            attach_dir = re.search(base_dir_re, _prefs)
            try:    
                attach_path = attach_dir.group(1)
            except:
                attach_path = None
            return [data_path, attach_path]

        # If only Firefox extension
        if os.path.exists(zf_pref_path):
            # Try to get data dir and linked attachments from Firefox prefs
            data_path = get_paths(zf_pref_path)[0]
            attach_path = get_paths(zf_pref_path)[1]
            default_path = zf_path

            if data_path == None:
                if os.path.exists(zs_pref_path):
                    # Try to get data directory from ZS prefs
                    data_path = get_paths(zs_pref_path)[0]
                    default_path = zs_path
            elif attach_path == None:
                if os.path.exists(zs_pref_path):
                    # Try to get linked attachments directory from ZS prefs
                    attach_path = get_paths(zs_pref_path)[1]
                    default_path = zs_path
            
        elif os.path.exists(zs_pref_path):
            data_path = get_paths(zs_pref_path)[0]
            attach_path = get_paths(zs_pref_path)[1]
            default_path = zs_path

        # Try paths to storage directory and zotero.sqlite file
        storage_path = os.path.join(data_path, 'storage')
        db_path = os.path.join(data_path, 'zotero.sqlite')

        # Check if prefs paths exist
        if os.path.exists(storage_path):
            pass
        else:
            # If not, have user select
            a_script = """
                set ui to load script POSIX file (POSIX path of "{0}")
                set choice to ui's choose_folder({{z_prompt:"Select Zotero storage folder.", z_def:"{1}"}})
            """.format(wf.workflowfile('_ui-helpers.scpt'), default_path)
            storage_path = applescript.asrun(a_script)[0:-1]

        if os.path.exists(db_path):
            pass
        else:
            a_script = """
                set ui to load script POSIX file (POSIX path of "{0}")
                set choice to ui's choose_file({{z_prompt:"Select Zotero sqlite database.", z_def:"{1}"}})
            """.format(wf.workflowfile('_ui-helpers.scpt'), default_path)
            db_path = applescript.asrun(a_script)[0:-1]

        if os.path.exists(attach_path): 
            pass
        else:
            a_script = """
                set ui to load script POSIX file (POSIX path of "{0}")
                set choice to ui's choose_folder({{z_prompt:"Select Zotero folder where linked attachments reside.", z_def:POSIX path of (path to documents folder)}})
            """.format(wf.workflowfile('_ui-helpers.scpt'))
            attach_path = applescript.asrun(a_script)[0:-1]

        # Store the paths in non-volatile storage
        with open(wf.datafile("paths.json"), 'w') as f:
            _dict = {'storage_path': storage_path, 
                    'database_path': db_path, 
                    'link-attachments_path': attach_path}
            _json = json.dumps(_dict, 
                                sort_keys=False, 
                                indent=4, 
                                separators=(',', ': '))
            f.write(_json.encode('utf-8'))
            f.close()


if __name__ == '__main__':
    wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
    sys.exit(wf.run(main))