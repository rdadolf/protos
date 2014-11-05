import logging
import json

# Protocol decorator
class protocol:
  def __init__(self,function):
    logging.debug('proto deco called')
    self._is_protocol = True
    self.function = function
  def __call__(self, *args, **kwargs):
    logging.debug('proto func called')
    return self.function(*args,**kwargs)


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


