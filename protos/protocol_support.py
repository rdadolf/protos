import sys
import logging
import json
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

# Shortcut to top-level project directory.
def home():
  return config.project_dir

# Convenience wrapper for subprocess
def call(cmd):
  # FIXME: do more here? maybe w/ logging
  logging.debug('Running "'+cmd+'"')
  proc = sub.Popen( cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE )
  ret=proc.wait()
  (out,err) = proc.communicate()
  (s_out,s_err) = (out.decode(sys.stdout.encoding),err.decode(sys.stderr.encoding))
  if len(s_out)>0:
    logging.debug(s_out)
  if len(s_err)>0:
    logging.error(s_err)
  assert ret==0, 'Failed to run "'+cmd+'"'
  return (out,err)

