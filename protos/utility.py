import sys
import logging
import os
import os.path

# The root directory is the top level home of the research project we're working
# on. We assume that basically everything is contained within this directory.
# FIXME: moving protos to its own program broke this. Fix it or find another way.
_protos_root_directory = None
def set_root():
  '''\
Sets the root directory of the protos project. Afterwards, can be accessed
by calling root().
'''
  global _protos_root_directory

  # First, check whether it's been explicitly set by PROTOS_ROOT
  try:
    _protos_root_directory = os.path.realpath(os.environ['PROTOS_ROOT'])
    return True
  except:
    pass

  # Next, try to pull it from the sys.argv[0] argument.
  # This assumes that protos.set_root() is called by a file in the project's
  # root directory. This isn't always true, but it's beter than nothing.
  if len(sys.argv[0])>0:
    _protos_root_directory = os.path.split(os.path.realpath(sys.argv[0]))[0]
    return True

  # Otherwise, we really have no idea, so throw a warning and use the CWD.
  logging.warning('No information for project root, using current directory.')
  _protos_root_directory = os.getcwd()

  return True

def root():
  '''
Returns the project's root directory, as set by protos.set_root().
'''
  global _protos_root_directory

  if _protos_root_directory is None:
    logging.error('You must call protos.set_root() before using protos.root()')
    # program exited
  return _protos_root_directory

# The data directory is the current working directory for the experiment we're
# running. FIXME: I'm not sure this is a good idea. Maybe it should be specified
# somewhere else instead.
_protos_data_directory = None
def data():
  '''
Returns the current experiment's root directory. This is set automatically.
'''
  if _protos_data_directory is None:
    loggig.error('No experiment directory found. This is probably a protos bug.')
  return _protos_data_directory
