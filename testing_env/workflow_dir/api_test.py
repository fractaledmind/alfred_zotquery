#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals
import re
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
            if library_type in ('user', 'group'):
                self.library_type = library_type + 's'
            else:
                raise RuntimeError('Invalid library type: %s' % library_type)
        if api_key:
            self.api_key = api_key
        self.request = None
        self.links = None

    def _retrieve_data(self, request=None, **kwargs):
        """
        Retrieve Zotero items via the API
        Combine endpoint and request to access the specific resource
        Returns an JSON object
        """
        full_url = '{}{}'.format(self.base, request)
        headers = {'User-Agent': "ZotQuery/{}".format(__version__),
                   'Authorization': "Bearer {}".format(self.api_key),
                   'Zotero-API-Version': 3}
        kwargs.update({'format': 'json'})
        self.request = web.get(url=full_url,
                               headers=headers,
                               params=kwargs)
        self.links = self._extract_links()
        self.request.raise_for_status()
        return self.request.json()

    def _prep_url(self, url, var=None):
        if var == None:
            return url.format(t=self.library_type,
                              u=self.library_id)
        else:
            return url.format(t=self.library_type,
                              u=self.library_id,
                              x=var)

    def _extract_links(self):
        try:
            links = self.request.headers['link']
            link_data = re.findall(r'<(.*?)>;\srel="(.*?)"', links)
            extracted = {}
            for link in link_data:
                url, key = link
                extracted[key] = url
            return extracted
        except KeyError:
            return None


    # No argument  -------------------------------------------------------------

    def items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items")
        return self._retrieve_data(url, **kwargs)

    def top_items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/top")
        return self._retrieve_data(url, **kwargs)

    def trash_items(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/trash")
        return self._retrieve_data(url, **kwargs)

    def tags(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/tags")
        return self._retrieve_data(url, **kwargs)

    def collections(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections")
        return self._retrieve_data(url, **kwargs)

    def top_collections(self, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/top")
        return self._retrieve_data(url, **kwargs)

    # Requires Argument  -------------------------------------------------------

    def item(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``dict``
        """
        url = self._prep_url("/{t}/{u}/items/{x}", item_id)
        return self._retrieve_data(url, **kwargs)

    def collection(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``dict``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}", collection_id)
        return self._retrieve_data(url, **kwargs)

    ## -------------------------------------------------------------------------

    def item_children(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/{x}/children", item_id)
        return self._retrieve_data(url, **kwargs)

    def item_tags(self, item_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/items/{x}/tags", item_id)
        return self._retrieve_data(url, **kwargs)

    def tag(self, tag_name, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/tags/{x}", tag_name)
        return self._retrieve_data(url, **kwargs)

    def collection_children(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}/collections", collection_id)
        return self._retrieve_data(url, **kwargs)

    def collection_items(self, collection_id, **kwargs):
        """Get items from Zotero

        :rtype: ``list``
        """
        url = self._prep_url("/{t}/{u}/collections/{x}/items", collection_id)
        return self._retrieve_data(url, **kwargs)

    #TODO: broken
    def follow(self):
        """ Return the result of the call to the URL in the 'Next' link
        """
        if self.links:
            url = self.links.get('next')
            return self._retrieve_data(url)
        else:
            return None

    ## -------------------------------------------------------------------------

    ## Full Reference Read API requests  ---------------------------------------

    def item_reference(self, item, **kwargs):
        info = self.item(item,
                         include='bib',
                         **kwargs)
        return info['bib']

    def tag_references(self, tag_name, **kwargs):
        info = self.items(include='bib',
                          tag=tag_name,
                          itemtype='-attachment || note',
                          **kwargs)
        return [x['bib'] for x in info]

    def collection_references(self, collection, **kwargs):
        info = self.collection_items(collection,
                                     include='bib',
                                     itemtype='-attachment || note',
                                     **kwargs)
        return [x['bib'] for x in info]

    ## -------------------------------------------------------------------------

    ## Short Citation Read API requests  ---------------------------------------

    def item_citation(self, item, **kwargs):
        info = self.item(item,
                         include='citation',
                         **kwargs)
        return info['citation']






def main(wf):
    """Accept Alfred's args and pipe to proper Class"""

    z = ZotAPI(library_id=wf.get_password('zotero_user'),
               library_type='user',
               api_key=wf.get_password('zotero_api'))
    print z.collection_references('5JBVB4Q4', style='apa')
    #print len(z.items(itemtype='book')
    #print z.tag('Mathematics')
    #print z.item('3KFT2HQ9', include='bib')
    #print type(z.item_children('3KFT2HQ9'))
    #print type(z.item_tags('3KFT2HQ9'))
    #print type(z.tag('Mathematics'))
    #print type(z.collection('5JBVB4Q4'))
    #print type(z.collection_children('5JBVB4Q4'))
    #print type(z.collection_items('5JBVB4Q4'))




    

if __name__ == '__main__':
    WF = Workflow()
    sys.exit(WF.run(main))
