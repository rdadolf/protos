# config_file
#
# Routines for finding and parsing config files.

import os
import sys
import warnings
import ConfigParser
from optparse import OptionParser

ENV_CONFIG_DIR = 'PROTOS_CONFIG_DIR'
DEFAULT_CONFIG_DIR = '$HOME/.protos/config/'

 # Dict of dicts
CONFIG_DEFAULTS = {
  'project' : {
    # Valid types are 'files','git','svn'
    'type' : 'files',

    # If project-type is 'git' or 'svn', project will be created if it does not
    # exist at that location already.
    'project-root' : '',

    # The path prefix(es) to search, in order, for protocol files.
    # Relative paths are relative to the 
    'protocol-path' : '',

    # Options for project-type=='git':
    'git-repo' : '',
    # Options
  }, 'log' : {
    # Valid types are 'files','git','svn'
    'type' : 'files',

    # If project-type is 'git' or 'svn', project will be created if it does not
    # exist at that location already.
    'log-root' : '',

    # Options for log-type=='git':
    'git-repo' : '',
    #'git-branch-by-project-revision' : False, FIXME?
  },
}
EXPAND_VARIABLES = [
  ('project','project-root'),
  ('project','protocol-path'),
  ('log','log-root'),
]

def expand_config_path(s):
  '''
  Given a string from a config function call, find the most likely absolute path.
  It's safe to repeatedly call expand_config_path() on a string: absolute paths
  take precendence over everything and expand_config_path always returns absolute
  paths if no error was encountered.
  '''
  # Absolute paths can be returned right away.
  if os.path.isabs(s):
    if os.path.exists(s):
      return s
    # If it's absolute and doesn't exist, don't go hunting. It's wrong.
    return None
  # Next, try the environment variable.
  env = os.getenv(ENV_CONFIG_DIR)
  if env is not None:
    path = os.path.join(env,s)
    if os.path.exists(path):
      return os.path.abspath(path)
  # No? Try the default config file directory.
  default = os.path.expandvars(DEFAULT_CONFIG_DIR)
  path = os.path.join(default,s)
  if os.path.exists(path):
    return os.path.abspath(path)
  # Still? Okay, last hope is that it's local.
  # (This is bad form because it's not portable. Hence why we try it last.)
  if os.path.exists(s):
    return os.path.abspath(s)
  # Nope. We fail.
  return None

def expand_protocol_path(protocol,paths):
  '''
  Takes a protocol name and a protocol path string, then searches for that
  protocol in the directories in the path.
  Also, try to append '.protocol' to the filename before moving on.
  '''
  suffix = '.protocol'
  for prefix in paths.split(':'):
    filename = os.path.join(prefix,protocol)
    if os.path.exists(filename):
      return os.path.abspath(filename)
    path = filename+suffix
    if os.path.exists(path):
      return os.path.abspath(path)
  return None
  

class Config:
  def __init__(self,filename=None):
    self._filename = None
    self._options = ConfigParser.SafeConfigParser()

    # We set defaults so that we never have to worry about checking
    # whether the dictionary *has* those options, only what they are.
    self.set_defaults()

    if filename is not None:
      self.parse(filename)

  # return True if found and parsed, False otherwise
  def find_config_file(self):
    # First, look on the command line
    parser = OptionParser()
    parser.add_option('-c','--config',dest='filename')
    (opt_dict,args) = parser.parse_args()
    if opt_dict.filename is not None:
      if self.parse(opt_dict.filename):
        return True
      else:
        warnings.warn('Failed to parse config file "'+str(opt_dict.filename)+'", searching for another.')
    # Next, look in the environment
    if 'PROTOS_CONFIG' in os.environ:
      if self.parse(os.environ['PROTOS_CONFIG']):
        return True
      else:
        warnings.warn('Failed to parse config file "'+str(opt_dict.filename)+'".')
    return False

  def get(self,sect,var):
    return self._options.get(sect,var)

  def set(self,sect,var,val):
    return self._options.set(sect,var,val)

  def set_defaults(self):
    for (section,dct) in CONFIG_DEFAULTS.items():
      if not self._options.has_section(section):
        self._options.add_section(section)
      for (key,val) in dct.items():
        self._options.set(section,key,str(val)) # Must be strings

  def parse(self,filename):
    path = expand_config_path(filename)
    assert path is not None, "Couldn't find a valid config file. Try -c <file> or setting PROTOS_CONFIG."
    self._filename = path
    assert os.path.exists(path) and os.path.isfile(path), "Couldn't find a valid config file. Try -c <file> or setting PROTOS_CONFIG."
    if( self._options.read(path)==[] ):
      # It didn't work. Blow the garbage away and reinitialize.
      self._filename = None
      self._options = ConfigParser.SafeConfigParser()
      self.set_defaults()
      return False
    return self.validate()

  def validate(self):
    # Expand environment variables in paths
    for (sec,var) in EXPAND_VARIABLES:
      tmp = self.get(sec,var)
      self.set(sec,var,os.path.expandvars(tmp))
    return True

  def expand_protocol_path(self, protocol_name):
    ''' Returns absolute path for protocol_name, based on project-path config variable.'''
    # Grab a couple of config variables
    proot = self.get('project','project-root')
    ppath = self.get('project','protocol-path')
    assert proot is not '', 'No project root specified in configuration file.'
    assert ppath is not '', 'No valid protocol paths specified in configuration file.'

    if not protocol_name.endswith('.protocol'): # defensive
      pname = protocol_name + '.protocol' # Add a .protocol extension automatically

    # Now search through the directories until we find one.
    for prefix in ppath.split(':'):
      if prefix=='':
        prefix='.'
      filename = os.path.join(prefix, pname)
      if os.path.isabs(prefix):
        if os.path.exists(filename):
          return filename
      else:
        filename = os.path.join(proot, filename)
        if os.path.exists(filename):
          return filename

    warnings.warn('Failed to expand protocol "'+str(protocol_name)+'"')
    return protocol_name
