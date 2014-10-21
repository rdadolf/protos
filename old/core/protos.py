'''
Protos is:
- A framework for setting up and running experimental protocols
- An archival storage solution with experiment snapshots for reproducibile results
- A Python-based eDSL which can bolt on to existing scripts
'''

import protocol
import workflow

def cache(data):
  print '[stub] CACHE'

def log(data):
  print '[stub] LOG'

def require(protocol):
  print '[stub] REQUIRE'

def tunnel(): #FIXME
  print '[stub] TUNNEL'

def var(name,value=None):
  print '[stub] VAR'
  return value
