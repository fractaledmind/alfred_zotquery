#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
sys.path.insert(0, 'alfred-workflow.zip')
import workflow
import os.path
import json
import zq_utils as z

####################################################################
# Action Class
####################################################################

class ZotAction(object):
    
    def __init__(self, _input, _action, data=[], settings=[], prefs=[]):
        self.wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
        self.input = _input
        self.action = _action

        if data == []:
            with open(self.wf.datafile("zotero_db.json"), 'r') as f:
                self.data = json.load(f)
                f.close()
        else: self.data = data

        if settings == []:
            with open(self.wf.datafile("settings.json"), 'r') as f:
                self.settings = json.load(f)
                f.close()
        else: self.settings = settings

        if prefs == []:
            with open(self.wf.datafile("prefs.json"), 'r') as f:
                self.prefs = json.load(f)
                f.close()
        else: self.prefs = prefs

        cache_files = ["temp_export.html", "temp_bibliography.txt", "temp_bibliography.html", "temp_attach_path.txt", "full_bibliography.html", "collection_query_result.txt", "tag_query_result.txt"]
        for file in cache_files:
            self.wf.cachefile(file)


    def act(self):
        if self.action == 'cite':
            return self.export_citation()
        elif self.action == 'ref':
            return self.export_ref()
        elif self.action == 'cite_group':
            return self.export_group()
        elif self.action == 'append':
            return self.append_to_bib()
        elif self.action == 'save_coll':
            self.save_collection()
        elif self.action == 'save_tag':
            self.save_tag()
        elif self.action == 'open':
            self.open_attachment()
        elif self.action == 'bib':
            return self.read_save_bib()


    ####################################################################
    # Export API methods
    ####################################################################

    def export_citation(self):
        item_id = self.input.split('_')[1]

        if self.prefs['csl'] == "odt-scannable-cites":
            self._export_scannable_cite()

        else:
            from pyzotero import zotero

            zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
            ref = zot.item(item_id, content='bib', style=self.prefs['csl'])
            uref = z.to_unicode(ref[0])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'citation')
                z.set_clipboard(citation.strip())

            elif prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'citation')
        return self.prefs['format']


    def export_ref(self):
        item_id = self.input.split('_')[1]

        if self.prefs['csl'] == 'odt-scannable-cites':
            self._export_scannable_cite()

        else:
            from pyzotero import zotero

            zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
            ref = zot.item(item_id, content='citation', style=self.prefs['csl'])
            uref = z.to_unicode(ref[0][6:-7])

            if self.prefs['format'] == 'Markdown':
                citation = self._export_markdown(uref, 'ref')
                z.set_clipboard(citation.strip())
                
            elif self.prefs['format'] == 'Rich Text':
                self._export_rtf(uref, 'ref')
        return self.prefs['format']

    
    def export_group(self):
        from pyzotero import zotero

        _inp = self.input.split(':')
        zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])

        if _inp[0] == 'c':
            cites = zot.collection_items(_inp[1], content='bib', style=self.prefs['csl'])
        elif _inp[0] == 't':
            cites = zot.tag_items(_inp[1], content='bib', style=self.prefs['csl'])

        if self.prefs['format'] == 'Markdown':
            import re, html2md

            md_cites = []
            for ref in cites:
                citation = html2md.html2text(ref)
                if self.prefs['csl'] != 'bibtex':
                    citation = re.sub("(?:http|doi)(.*?)$|pp. ", "", citation)
                    citation = re.sub("_(.*?)_", "*\\1*", citation)
                md_cites.append(citation)

            sorted_md = sorted(md_cites)
            sorted_md.insert(0, 'WORKS CITED\n')
            z.set_clipboard('\n'.join(sorted_md))

        elif self.prefs['format'] == 'Rich Text':
            from dependencies import applescript
            import re

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                for ref in cites:
                    f.write(ref.encode('ascii', 'xmlcharrefreplace'))
                    f.write('<br>')
                f.close()

            with open(self.wf.cachefile("full_bibliography.html"), 'r') as f:
                bib_html = f.read()
                f.close()
            
            if prefs['csl'] != 'bibtex':
                bib_html = re.sub(r"http(.*?)\.(?=<)", "", bib_html)
                bib_html = re.sub(r"doi(.*?)\.(?=<)", "", bib_html)
            bib_html = re.sub("pp. ", "", bib_html)
            
            html_cites = bib_html.split('<br>')
            sorted_html = sorted(html_cites)
            sorted_html.insert(0, 'WORKS CITED<br>')
            final_html = '<br>'.join(sorted_html)

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                f.write(final_html)
                f.close()

            a_script = """
                do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
                """.format(self.wf.cachefile("full_bibliography.html"))
            applescript.asrun(a_script)

            with open(self.wf.cachefile("full_bibliography.html"), 'w') as f:
                f.write('')
                f.close()
        return self.prefs['format']


    def append_to_bib(self):
        from pyzotero import zotero

        item_id = self.input.split('_')[1]

        zot = zotero.Zotero(self.settings['user_id'], self.settings['type'], self.settings['api_key'])
        ref = zot.item(item_id, content='bib', style=self.prefs['csl'])
        uref = z.to_unicode(ref[0])

        if self.prefs['format'] == 'Markdown':
            citation = self._export_markdown(uref, 'citation')
            with open(self.wf.cachefile("temp_bibliography.txt"), 'a') as f:
                f.write(citation.strip())
                f.write('\n\n')
                f.close()

        elif self.prefs['format'] == 'Rich Text':
            with open(self.wf.cachefile("temp_bibliography.html"), 'a') as f:
                f.write(uref[23:])
                f.write('<br>')
                f.close
        return self.prefs['format']

    ####################################################################
    # Export helper functions
    ####################################################################

    def _export_markdown(self, html, style):
        from dependencies import html2md
        
        if self.prefs['csl'] != 'bibtex':
            import re
            html = re.sub("(?:http)(.*?)$|pp. ", "", html)
        
        citation = html2md.html2text(html)
        if style == 'citation':
            citation = re.sub("_(.*?)_", "*\\1*", citation)
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                citation = '[@' + citation.strip() + ']'
        return citation

    def _export_rtf(self, html, style):
        import applescript

        if self.prefs['csl'] != 'bibtex':
            import re
            html = re.sub("(?:http)(.*?)$|pp. ", "", html)

        if style == 'citation':
            html = html.encode('ascii', 'xmlcharrefreplace')[23:]
        elif style == 'ref':
            if self.prefs['csl'] == 'bibtex':
                html = '[@' + html.strip() + ']'    
            html = html.encode('ascii', 'xmlcharrefreplace')

        with open(self.wf.cachefile("temp_export.html"), 'w') as f:
            f.write(html)
            f.close
        a_script = """
            do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
            """.format(self.wf.cachefile("temp_export.html"))
        applescript.asrun(a_script)


    def _export_scannable_cite(self):
        item_id = self.input.split('_')[1]
        uid = self.settings['user_id']
        z.set_clipboard(z.scan_cites(self.data, item_id, uid))
        return self.prefs['format']


    ####################################################################
    # Save API methods
    ####################################################################

    def save_collection(self):
        with open(self.wf.cachefile("collection_query_result.txt"), 'w') as f:
            f.write(self.input.encode('utf-8'))
            f.close()

    def save_tag(self):
        with open(self.wf.cachefile("tag_query_result.txt"), 'w') as f:
            f.write(self.input.encode('utf-8'))
            f.close()

    def read_save_bib(self):
        if self.prefs['format'] == 'Markdown':
            with open(self.wf.cachefile("temp_bibliography.txt"), 'r') as f:
                bib = f.read()
                f.close()
            sorted_l = sorted(bib.split('\n\n'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED'
            else:
                sorted_l.insert(0, 'WORKS CITED')
            z.set_clipboard('\n\n'.join(sorted_l))

            return self.prefs['format']
            with open(self.wf.cachefile("temp_bibliography.txt"), 'w') as f:
                f.write('')
                f.close()

        elif self.prefs['format'] == 'Rich Text':
            with open(self.wf.cachefile("temp_bibliography.html"), 'r') as f:
                bib = f.read()
                f.close()
            sorted_l = sorted(bib.split('<br>'))
            if sorted_l[0] == '':
                sorted_l[0] = 'WORKS CITED<br>'
            else:
                sorted_l.insert(0, 'WORKS CITED<br>')
            html_string = '<br><br>'.join(sorted_l)
            # Write html to temporary bib file
            with open(self.wf.cachefile("temp_bibliography.html"), 'w') as f:
                f.write(html_string)
                f.close()
            # Convert html to RTF and copy to clipboard
            a_script = """
                do shell script "textutil -convert rtf " & quoted form of "{0}" & " -stdout | pbcopy"
                """.format(self.wf.cachefile("temp_bibliography.html"))
            applescript.asrun(a_script)

            return self.prefs['format']
            # Write blank file to bib file
            with open(self.wf.cachefile("temp_bibliography.html"), 'w') as f:
                f.write('')
                f.close()


    ####################################################################
    # Attachment API method
    ####################################################################

    def open_attachment(self):
        import os.path, subprocess, applescript

        if os.path.isfile(self.input):
            subprocess.Popen(['open', self.input], shell=False, stdout=subprocess.PIPE)
        # if self.input is item key
        else:
            # Get the item's attachement path and attachment key
            item_id = self.input.split('_')[1]
            for item in self.data:
                if item_id == item['key']:
                    for jtem in item['attachments']:
                        path = jtem['path']
                        key = jtem['key']

                        if os.path.isfile(path):
                            subprocess.Popen(['open', path], shell=False, 
                                            stdout=subprocess.PIPE)
                        else:
                            # Open the attachment in Zotero
                            a_script = """
                            if application id "org.zotero.zotero" is not running then
                                tell application id "org.zotero.zotero" to launch
                            end if
                            delay 0.5
                            tell application id "org.zotero.zotero"
                                activate
                                delay 0.3
                                open location "zotero://select/items/0_{0}"
                            end tell
                            """.format(key)
                            applescript.asrun(a_script)


####################################################################
# Main Function
####################################################################

def main(wf):
    """Access and run class methods"""

    _query = wf.args[0]
    _action = wf.args[1]
    #_query = '0_ZU6PGWNA'
    #_action = 'cite'
    za = ZotAction(_query, _action)
    print za.act()


if __name__ == '__main__':
    wf = workflow.Workflow(libraries=[os.path.join(os.path.dirname(__file__), 'dependencies')])
    sys.exit(wf.run(main))
