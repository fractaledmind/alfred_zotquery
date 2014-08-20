#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import sys
import json

from workflow import Workflow, web

__version__ = '10.0'


class ZotAPI(object):
    """
    Zotero API (v.3) methods
    """
    def __init__(self, library_id=None, library_type=None, api_key=None):
        """ Store Zotero credentials
        """
        self.base = 'https://api.zotero.org'
        if library_id and library_type:
            self.library_id = library_id
            if library_type in ('user', 'group', 'users', 'groups'):
                if library_type.endswith('s'):
                    self.library_type = library_type
                else:
                    self.library_type = library_type + 's'
        if api_key:
            self.api_key = api_key
        self.urls = {
            'items': "/{t}/{u}/items",
            'items_top': "/{t}/{u}/items/top",
            'items_trash': "/{t}/{u}/items/trash",
            'item': "/{t}/{u}/items/{i}",
            'item_sub': "/{t}/{u}/items/{i}/children",
            'item_tags': "/{t}/{u}/items/{i}/tags",
            'tags': "/{t}/{u}/tags",
            'tag': "/{t}/{u}/tags/{e}",
            'tag_items': "/{t}/{u}/tags/{ta}/items",
            'collections': "/{t}/{u}/collections",
            'collections_top': "/{t}/{u}/collections/top",
            'collection': "/{t}/{u}/collections/{c}",
            'collections_sub': "/{t}/{u}/collections/{c}/collections",
            'collection_items': "/{t}/{u}/collections/{c}/items",
        }

    def _retrieve_data(self, request=None, params={}):
        """
        Retrieve Zotero items via the API
        Combine endpoint and request to access the specific resource
        Returns an JSON object
        """
        full_url = '{}{}'.format(self.base, request)
        headers = {'User-Agent': "ZotQuery/{}".format(__version__),
                   'Authorization': "Bearer {}".format(self.api_key),
                   'Zotero-API-Version': 3}
        params.update({'format': 'json'})
        self.request = web.get(url=full_url,
                               headers=headers,
                               params=params)

        self.request.raise_for_status()
        return self.request.json()

    ## -------------------------------------------------------------------------

    ## Generic Read API requests  ----------------------------------------------

    def get_item(self, item, params):
        url = self.urls.get('item')
        url = url.format(t=self.library_type,
                         u=self.library_id,
                         i=item.upper())
        return self._retrieve_data(url, params=params)

    def get_tag_items(self, tag, params):
        url = self.urls.get('items')
        url = url.format(t=self.library_type,
                         u=self.library_id,
                         ta=tag)
        params.update({'tag': tag})
        params.update({'itemType': '-attachment || note' })
        return self._retrieve_data(url, params=params)

    def get_collection_items(self, collection, params):
        url = self.urls.get('collection_items')
        url = url.format(t=self.library_type,
                         u=self.library_id,
                         c=collection)
        params.update({'itemType': '-attachment || note' })
        return self._retrieve_data(url, params=params)

    ## -------------------------------------------------------------------------

    ## Full Reference Read API requests  ---------------------------------------

    def item_reference(self, item, **kwargs):
        return self._get_template('bib',
                                  self.get_item,
                                  item,
                                  **kwargs)

    def tag_references(self, tag, **kwargs):
        return self._get_template('bib',
                                  self.get_tag_items,
                                  tag,
                                  **kwargs)

    def collection_references(self, collection, **kwargs):
        return self._get_template('bib',
                                  self.get_collection_items,
                                  collection,
                                  **kwargs)

    ## -------------------------------------------------------------------------

    ## Short Citation Read API requests  ---------------------------------------

    def item_citation(self, item, **kwargs):
        return self._get_template('citation',
                                  self.get_item,
                                  item,
                                  **kwargs)

    def tag_citations(self, tag, **kwargs):
        return self._get_template('citation',
                                  self.get_tag_items,
                                  tag,
                                  **kwargs)

    def collection_citations(self, collection, **kwargs):
        return self._get_template('citation',
                                  self.get_collection_items,
                                  collection,
                                  **kwargs)
        

    def _get_template(self, type, func, item, **kwargs):
        if 'style' not in kwargs.keys():
            kwargs.update({'style': 'chicago-author-date'})
        kwargs.update({'include': type})
        data = func(item, kwargs)
        try:
            return [item[type] for item in data]
        except TypeError:
            return data[type]







def main(wf):
    """Accept Alfred's args and pipe to proper Class"""

    z = ZotAPI(library_id=wf.get_password('zotero_user'),
               library_type='user',
               api_key=wf.get_password('zotero_api'))
    #print z.get_item('3KFT2HQ9', include='bib', style=apa')
    #print z.get_tag_items('Mathematics', include='citation', style='apa')
    #print z.get_collection_items('5JBVB4Q4', include='citation')
    
    print z.item_reference('3KFT2HQ9', style='apa')
    #print z.tag_references('Mathematics')
    #print z.collection_references('5JBVB4Q4')

    #print z.item_citation('3KFT2HQ9')
    #print z.tag_citations('Mathematics')
    #print z.collection_citations('5JBVB4Q4')





    

if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
