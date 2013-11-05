# config_file
#
# Routines for finding and parsing config files.

import os
import ConfigParser

ENV_CONFIG_DIR = 'PROTOS_CONFIG_DIR'
DEFAULT_CONFIG_DIR = '$HOME/.protos/config/'

 # Dict of dicts
CONFIG_DEFAULTS = {
  'project' : {
    'repo' : '',
    'protocol-path' : '', # ordered sequence of :-separated paths
    },
  'log' : {
    'repo' : '',
    },
  }

def expand_config_path(s):
  '''
  Given a string from a config function call, find the most likely absolute path.
  It's safe to repeatedly call expand_config_path() on a string: absolute paths
  take precendence over everything and expand_config_path always returns absolute
  paths if no error was encountered.
  '''
  # Absolute paths can be returned right away.
  if os.path.isabs(s):
    return s
  # Next, try the environment variable.
  env = os.getenv(ENV_CONFIG_DIR)
  if env is not None:
    path = os.path.join(env,s)
    if os.path.exists(path):
      return path
  # No? Try the default config file directory.
  default = os.path.expandvars(DEFAULT_CONFIG_DIR)
  path = os.path.join(default,s)
  if os.path.exists(path):
    return path
  # Still? Okay, last hope is that it's local.
  # (This is bad form because it's not portable. Hence why we try it last.)
  if os.path.exists(s):
    return os.path.abspath(s)
  f=open(s) # Relative path that doesn't seem to exist. This forces the error.
  return None

def expand_protocol_path(protocol,paths):
  '''
  Takes a protocol name and a protocol path string, then searches for that
  protocol in the directories in the path.
  '''
  for prefix in paths.split(':'):
    filename = os.path.join(prefix,protocol)
    if os.path.exists(filename):
      return filename
  return None
  

class Config:
  def __init__(self,filename=None):
    self._filename = None
    self._options = ConfigParser.SafeConfigParser()
    self.set_defaults()
    if filename is not None:
      self.parse(filename)

  def set_defaults(self):
    for (section,dct) in CONFIG_DEFAULTS.items():
      if not self._options.has_section(section):
        self._options.add_section(section)
      for (key,val) in dct.items():
        self._options.set(section,key,str(val)) # Must be strings

  def parse(self,filename):
    path = expand_config_path(filename)
    self._filename = path
    if( self._options.read(path)==[] ):
      # It didn't work. Blow the garbage away and reinitialize.
      self._filename = None
      self._options = ConfigParser.SafeConfigParser()
      self.set_defaults()
      return False
    return True

  def get(self,sect,var):
    return self._options.get(sect,var)
