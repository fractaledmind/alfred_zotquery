#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import json
import os.path
import unittest
import subprocess
from StringIO import StringIO

# Dependencies
import zotquery as z
import bundler
bundler.init()
import xmltodict


EXPECTED_COLL = """WORKS CITED

Allen, James V. 2001. *Inference from Signs: Ancient Debates About the Nature of Evidence*. Oxford University Press.

Barnes, Jonathan. 2001. *Early Greek Philosophy*. Penguin. 

Dihle, A. 1962. “Aus Herodots Gedankenwelt.” *Gymnasium* 69: 22.

Dihle, Albrecht. 1962. “Herodot Und Die Sophistik.” *Philologus* 106 (1062): 207–220.

Fehling, Detlev, and J. G. Howie. 1990. *Herodotus and His“ Sources”: Citation, Invention, and Narrative Art*. Francis Cairns. 

Fowler, Robert L. 1996. “Herodotos and His Contemporaries.” *Journal of Hellenic Studies*: 62–87. 

Gentzler, Jyl. 2001. *Method in Ancient Philosophy*. Oxford University Press.

Graham, Daniel W. 2003. “Philosophy on the Nile: Herodotus and Ionian Research.” *Apeiron* 36 (4): 291–310. 

Grimaldi, W. M. A. 1980. “Semeion, Tekmerion, Eikos in Aristotle’s Rhetoric.” *The American Journal of Philology* 101 (4): 383. doi:10.2307/293663. 

Jouanna, Jacques. 1996. *Hippocrate Tome II: Airs, Eaux, Lieux*. Paris: Les Belles lettres.

Lateiner, Donald. 1986. “The Empirical Element in the Methods of Early Greek Medical Writers and Herodotus: a Shared Epistemological Response.” *Antichthon* 20: 1. 

Lear, Jonathan. 1988. *Aristotle: The Desire to Understand*. Cambridge [Cambridgeshire]; New York: Cambridge University Press.

Lloyd, Geoffrey Ernest Richard. 1966. *Polarity and Analogy: Two Types of Argumentation in Early Greek Thought*. Cambridge Univ Press. 

Morrison, John Sinclair. 1956. “Airs, Waters, Places, XVI.” *Classical Review* 1956 (VI, N.S.): 102–1.

Nestle, Wilhelm. 1908. *Herodots Verhältnis Zur Philosophie Und Sophistik...* Druck der Stuttgarter Vereinsbuchdruckerei.

Noël, Marie-Pierre. 2011. “Isocrates and the Rhetoric to Alexander: Meaning and Uses of Tekmerion.” *Rhetorica: A Journal of the History of Rhetoric* 29 (3) (August): 319–335. doi:10.1525/RH.2011.29.3.319. 

Reguero, M. Carmen Encinas. 2009. “La Evolución de Algunos Conceptos Retóricos. Semeion y Tekmerion Del S. V Al IV a.C.” *Rhetorica* 27 (4) (November): 373–403. doi:10.1525/RH.2009.27.4.373. 

Thomas, Rosalind. 1998. “Ethnography, Proof and Argument in Herodotus’ Histories.” *The Cambridge Classical Journal* 43. New Series: 128–48.

Thomas, Rosalind. 2000. *Herodotus in Context: Ethnography, Science and the Art of Persuasion*. Cambridge, UK: Cambridge Univ. Press.

Van der Eijk, Philip. 1997. “Towards a Rhetoric of Ancient Scientific Discourse.” In *Grammar as Interpretation: Greek Literature in Its Linguistic Contexts*, edited by Egbert Bakker. Leiden: Brill.

Vlastos, Gregory. 1996. *Studies in Greek Philosophy: The Presocratics*. Princeton University Press.

Ward, Ann. 2008. *Herodotus and the Philosophy of Empire*. Baylor University Press. 
"""

EXPECTED_TAG = """WORKS CITED

Vermeulen, C. F. M. 2000. “Text Structure and Proof Structure.” *Journal of Logic, Language and Information* 9 (3) (July 1): 273–311. doi:10.1023/A:1008309715242. 
"""

def setUp():
    pass

def tearDown():
    pass

def to_unicode(obj, encoding='utf-8'):
    """Detects if object is a string and if so converts to unicode"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def get_clipboard(): 
    """Get objects of clipboard"""
    os.environ['__CF_USER_TEXT_ENCODING'] = "0x1F5:0x8000100:0x8000100"
    proc = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    proc.wait()
    data = proc.stdout.read()
    return to_unicode(data)

def capture_output(zot_filter):
    """Capture `sys` output in var"""
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    zot_filter.filter()
    sys.stdout = old_stdout
    res_dict = xmltodict.parse(mystdout.getvalue())
    return res_dict


class FilterTests(unittest.TestCase):
    """Test the Filters"""

    def setUp(self):
        test_path = os.path.join(os.path.dirname(__file__), '__test.json')
        with open(test_path, 'r') as file_obj:
            self.data = json.load(file_obj)
            file_obj.close()
        self.scopes = ['general', 'creators', 'titles', 'notes', 
                        'collections', 'tags', 
                        'in-collection', 'in-tag', 
                        'attachments']
        self.colls = [["Epicureanism in Horace's Satires", "5JBVB4Q4"],
                        ["Epi Semiosis in Vergil", "K4Q262P7"]]
        self.tags = [["Satire 1.3", "UZG6NWWI"]]

    ####################################################################
    # Filter Tests
    ####################################################################

    # General Scope ----------------------------------------------
    def test_filter_general(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('fernandez biosemio', self.scopes[0],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['arg'],
                        "266264_T3IT8DJD")

    # Creators Scope ----------------------------------------------
    def test_filter_creators(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('rösen', self.scopes[1],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['title'],
                        "Making mockery: the poetics of ancient satire")

    # Titles Scope ----------------------------------------------
    def test_filter_titles(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('ποδιαία', self.scopes[2],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['title'],
                        "In what proof would a geometer use the ποδιαία ?")

    # Notes Scope ----------------------------------------------
    def test_filter_notes(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('follow values', self.scopes[3],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['subtitle'],
            "Putnam. 1995. Attachments: 1")
        
    # Collections Scope ----------------------------------------------
    def test_filter_collections_len(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('semiosis', self.scopes[4],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['title'],
                        "Epi Semiosis in Vergil")

    # Tags Scope ----------------------------------------------
    def test_filter_tags(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('math', self.scopes[5],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        self.assertEqual(res_dct['items']['item']['title'],
                        "Mathematics")

    # In-Collection Scope ----------------------------------------------
    def test_filter_incollection(self):
        """Test `general` scope"""
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        z.ZotFilter('horace', self.scopes[6],
                    test_data=self.data, test_group="K4Q262P7")
        sys.stdout = old_stdout
        res_dct = xmltodict.parse(mystdout.getvalue())
        self.assertEqual(res_dct['items']['item']['subtitle'],
                        "Sharland. 2009.")

    # In-Tag Scope ----------------------------------------------
    def test_filter_intag(self):
        """Test `general` scope"""
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        z.ZotFilter('aequabilitas', self.scopes[7],
                        test_data=self.data, test_group="UZG6NWWI")
        sys.stdout = old_stdout
        res_dct = xmltodict.parse(mystdout.getvalue())
        self.assertEqual(res_dct['items']['item']['icon'],
                        "icons/att_article.png")

    # Attachments Scope ----------------------------------------------
    def test_filter_attachment(self):
        """Test `general` scope"""
        zot_filter = z.ZotFilter('irony kemp', self.scopes[8],
                                 test_data=self.data)
        res_dct = capture_output(zot_filter)
        base = "/Users/smargheim/Documents/PDFs/Zotero/"
        path = "kemp_2009_irony and aequabilitas _journal article.pdf"
        self.assertEqual(res_dct['items']['item']['arg'],
            base + path)


"""
class ActionTests(unittest.TestCase):

    def setUp(self):
        self.prefs = {"format": "Markdown",
                      "csl": "chicago-author-date",
                      "client": "Standalone"}
        self.settings = {"api_key": "rf8L5AZdrVlK9NMTXDVuotok",
                         "type": "user",
                         "user_id": "1140739"}

    ####################################################################
    # Action Tests
    ####################################################################

    def test_action_export_citation(self):
        "Test full citation action"
        zot_action = z.ZotAction("0_C3KEUQJW", "cite",
                        settings=self.settings, prefs=self.prefs)
        zot_action.act()
        self.assertEqual(get_clipboard(),
            "Margheim, Stephen. 2013. “Test Item.” *A Sample Publication* 1 (1): 1–14.")
        
    def test_action_export_ref(self):
        Test full citation action"
        zot_action = z.ZotAction("0_C3KEUQJW", "ref",
                        settings=self.settings, prefs=self.prefs)
        zot_action.act()
        self.assertEqual(get_clipboard(),
            "(Margheim 2013)")

    def test_action_export_collection(self):
        Test full citation action"
        zot_action = z.ZotAction("c:NHAEA4EJ", "cite_group",
            settings=self.settings, prefs=self.prefs)
        zot_action.act()
        self.assertEqual(get_clipboard(), EXPECTED_COLL)

    def test_action_export_tag(self):
        Test full citation action"
        zot_action = z.ZotAction("t:Semantics", "cite_group",
            settings=self.settings, prefs=self.prefs)
        zot_action.act()
        self.assertEqual(get_clipboard(), EXPECTED_TAG)
"""



if __name__ == '__main__':
    unittest.main()
