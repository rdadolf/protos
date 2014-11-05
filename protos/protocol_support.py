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
    self.function(*args,**kwargs)


#def protocol(func):
#  logging.debug('Found protocol "'+str(func.__name__)+'"')
#  
#  def protocol_appender(*args, **kwargs):
#    logging.debug('PAppend kwargs: '+str(kwargs.keys()))
#    logging.debug('PAppend globs: '+str(globals().keys()))
#    # FIXME: how do I get a reference to _experiment here?
#    _experiment.append( func, args, kwargs )
#    db_tok = Bundle_Token.new()
#    return lambda : db_tok
#    # Note, this decorator returns a thunk that is *very* unlike the original
#    # function that we defined. Instead of executing, it just returns a token
#    # that can be used to reference the answer later in the experiment. These
#    # will be replaced with actual Data_Bundles at run time.
#
#  # Tag the function as a protocol
#  protocol_appender._is_protocol = True
#
#  return protocol_appender # this will be executed (and it will return a token)


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


