#!/usr/bin/python
# encoding: utf-8
from workflow import Workflow
WF = Workflow()

from zotero import api
from backend import data


class ZotQuery(object):
    def __init__(self):
        self._backend = data(WF)
        self._web = api(WF)
        self._local = self._backend.zotero

    @property
    def backend(self):
        return self._backend

    @property
    def web(self):
        return self._web

    @property
    def local(self):
        return self._local

zq = ZotQuery()
