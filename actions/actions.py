#!/usr/bin/python
# encoding: utf-8
import sys
sys.path.insert(0, 'alfred-workflow.zip')
import workflow
from zq_actions import ZotAction

def main(wf):
	query = wf.args[0]
	action = wf.args[1]
	#query = '0_ZU6PGWNA'
	#action = 'cite'
	za = ZotAction(query, action)
	print za.act()

if __name__ == '__main__':
	wf = workflow.Workflow()
	sys.exit(wf.run(main))