'''
Protos is:
- A framework for setting up and running experimental protocols
- An archival storage solution with experiment snapshots for reproducibile results
- A Python-based eDSL which can bolt on to existing scripts
'''

import protocol
import workflow

def config(protocol):
  print '[stub] CONFIG'

def require(protocol):
  print '[stub] REQUIRE'

def cache(data):
  print '[stub] CACHE'

def log(data):
  print '[stub] LOG'

def var(name,value=None):
  print '[stub] VAR'
  return value
