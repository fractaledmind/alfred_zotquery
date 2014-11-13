#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 stephen.margheim@gmail.com
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

# Standard Library
import sys

# Internal Dependencies
from zotquery import config
from zotquery.lib.docopt import docopt

# Alfred-Workflow
from workflow import Workflow
from zotquery import search, export, append, store, open, configure, scan

# create global methods from `Workflow()`
WF = Workflow(update_settings={
    'github_slug': 'smargh/alfred_zotquery',
    'version': config.__version__,
    'frequency': 7
})


class ZotWorkflow(object):
    """Represents all the Alfred Workflow actions.

    :param wf: a :class:`Workflow` instance.
    :type wf: :class:`object`

    """
    def __init__(self, wf):
        self.wf = wf
        self.flag = None
        self.arg = None

  #----------------------------------------------------------------------------
  ## Main API methods
  #----------------------------------------------------------------------------

    def run(self, args):
        """Main API method.

        :param args: command line arguments passed to workflow
        :type args: :class:`dict`
        :returns: whatever the `method` returns
        :rtype: UNKOWN (see ind. methods for info)

        """
        self.flag = args['<flag>']
        self.arg = args['<argument>']
        # list of all possible actions
        actions = ('search', 'export', 'append', 'store',
                   'open', 'configure', 'scan')
        for action in actions:
            if args.get(action):
                method_name = '{}_codepath'.format(action)
                method = getattr(self, method_name, None)
                if method:
                    return method()
                else:
                    raise ValueError('Unknown action: {}'.format(action))

    def search_codepath(self):
        return search.search(self.flag, self.arg, self.wf)

    def export_codepath(self):
        return export.export(self.flag, self.arg, self.wf)

    def append_codepath(self):
        return append.append(self.flag, self.arg, self.wf)

    def store_codepath(self):
        return store.store(self.flag, self.arg, self.wf)

    def open_codepath(self):
        return open.open(self.flag, self.arg, self.wf)

    def configure_codepath(self):
        return configure.configure(self.flag, self.arg, self.wf)

    def scan_codepath(self):
        return scan.scan(self.flag, self.arg, self.wf)


def main(wf):
    """Accept Alfred's args and pipe to workflow class"""
    if wf.update_available:
        wf.start_update()

    config.log.info('- - - NEW RUN - - -')
    args = wf.args
    #args = ['search', 'creators', 'margheim']
    #args = ['export', 'bib', '0_3KFT2HQ9']
    #args = ['append', 'citation', '0_3KFT2HQ9']
    #args = ['store', 'tag', 't_XK9QHQ6G']
    #args = ['open', 'item', '0_3KFT2HQ9']
    #args = ['configure', 'freshen']
    argv = docopt(config.__usage__,
                  argv=args,
                  version=config.__version__)
    config.log.info('Input arguments : {}'.format(args))
    pd = ZotWorkflow(wf)
    res = pd.run(argv)
    if res:
        print(res)

if __name__ == '__main__':
    sys.exit(WF.run(main))
