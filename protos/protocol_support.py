import logging
import json
import os
import os.path
import shutil
import tempfile

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

# Python context for temporary directory
class scratch_directory:
  def __init__(self, debug=False):
    self.debug = debug # Preservers contents of 
    self.dir = None
  def __enter__(self):
    self.dir = tempfile.mkdtemp(prefix='/tmp/protos_temp_')
    logging.debug('Creating scratch directory '+self.dir)
    return self.dir
  def __exit__(self, type, value, traceback):
    if not self.debug:
      logging.debug('Cleaning up scratch directory '+self.dir)
      # recursively delete whatever is in the scratch space
      assert os.path.isdir(self.dir), 'Scratch directory not found--something is wrong'
      assert len(self.dir)>1, 'Bad scratch directory name: "'+str(self.dir)+'"'
      shutil.rmtree(self.dir)
    return False # Don't suppress errors

# Metadata reading/writing
def read_metadata(file): # returns dictionary
  '''
  Reads a metadata file and returns a python dictionary of its contents.
  '''
  with open(file) as f:
    d=json.load(f)
    return d

def write_metadata(file,md):
  '''
  Writes a dictionary into a metadata file for later use.
  '''
  with open(file,'w') as f:
    json.dump(md,f,indent='2')


