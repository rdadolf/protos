import sys
import logging
import subprocess as sub

from .data_bundles import Data_Bundle
from .config import config

# Protocol decorator
class protocol:
  def __init__(self,function):
    #logging.debug('proto deco called')
    self._is_protocol = True
    self.function = function
    self.__name__ = str(function.__name__)+'-thunk'
  def __call__(self, *args, **kwargs):
    #logging.debug('proto func called')
    return self.function(*args,**kwargs)


### Protocol support functions for users ###

# Convenience wrapper for subprocess
def call(cmd):
  # FIXME: do more here? maybe w/ logging
  logging.debug('Running "'+cmd+'"')
  proc = sub.Popen( cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines = True )
  (out,err) = proc.communicate()
  ret = proc.returncode
  if len(out)>0:
    for l in out.split('\n'):
      logging.debug(l)
  if len(err)>0:
    for l in err.split('\n'):
      logging.error(l)
  assert ret==0, 'Failed to run "'+cmd+'"'
  return (out,err)

