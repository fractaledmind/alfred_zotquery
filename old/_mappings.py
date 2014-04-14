#!/usr/bin/python
# encoding: utf-8
import os
import re
from zq_utils import to_unicode


class ZotMap(object):
    """
    Class to translate Zotero's key names to standard CSL-JSON names.
    The mapping relationships are defined in the _zotero-csl_mappings.json file. 
    Since JSON is not ideal for value-based queries, 
    and since parsing the entire tree as XML on each call takes too much time, 
    these functions utilize merely Regular Expressions.
    """

    def __init__(self):
        mappings_path = os.getcwd() + '/_zotero-csl_mappings.json'
        self.mappings = open(mappings_path).read()

    ####################################################################
    # Main API methods
    ####################################################################

    def trans_fields(self, _qu, _goal):
        """Translate Field"""
        
        return self._translate(_qu, 'field', _goal)    
        

    def trans_types(self, _qu, _goal):
        """Translate Types"""

        return self._translate(_qu, 'type', _goal) 

            
    def trans_creators(self, _qu, _goal):
        """Translate Creators"""

        return self._translate(_qu, 'field', _goal) 

    ####################################################################
    # Helper methods
    ####################################################################

    def _regex(self, _qu, _type, _goal):
        """Returns appropriate compiled regex for translation type"""

        if _type == 'field':
            if _goal == 'csl':
                return r'"@zField":\s"' + _qu + r'",\n\s*"@cslField":\s"(.*?)"$'
            elif _goal == 'zot':
                return r'"@zField":\s"(.*?)",\n\s*"@cslField":\s"' + _qu + r'"$'
        elif _type == 'base':
            if _goal == 'csl':
                return r'"@value":\s"' + _qu + r'",\n\s*"@baseField":\s"(.*?)"$'
            elif _goal == 'zot':
                return r'"@value":\s"(.*?)",\n\s*"@baseField":\s"' + _qu + r'"$'
        elif _type == 'type':
            if _goal == 'csl':
                return r'"@zType":\s"' + _qu + r'",\n\s*"@cslType":\s"(.*?)"'
            elif _goal == 'zot':
                return r'"@zType":\s"(.*?)",\n\s*"@cslType":\s"' + _qu + r'"'


    def _search(self, _qu, _type, _goal):
        """Find field types"""

        if _type == 'field':
            _re = self._regex(_qu, 'field', _goal)
        elif _type == 'type':
            _re = self._regex(_qu, 'type', _goal)

        _res = re.findall(_re, self.mappings, re.M)
        if not _res == []:
            return  _res[0]
        else:
            return None


    def _translate(self, _qu, _type, _goal):
        """Central method to translate names"""
        # See if Zotero field has direct mapping to CSL
        _res = self._search(_qu, _type, _goal)
        
        if _res == None:
            # If not, search for the base field of that particular field
            _re = self._regex(_qu, 'base', _goal)
            _res = re.findall(_re, self.mappings, re.M)
            if not _res == []:
                res = self._search(_res[0], _type, _goal)
                return to_unicode(res)
            else:
                return to_unicode(_qu)
        else:
            return to_unicode(_res)
