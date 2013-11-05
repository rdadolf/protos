'''
Protos is:
- A framework for setting up and running experimental protocols
- An archival storage solution with experiment snapshots for reproducibile results
- A Python-based eDSL which can bolt on to existing scripts
'''

import protocol
import workflow

def config(protocol):
  print 'CONFIG'

def require(protocol):
  print workflow.__name__
  print 'REQUIRE'

def log(data):
  print 'LOG'

def var(name,value=None):
  print 'VAR'

