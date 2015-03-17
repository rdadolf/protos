import logging
import json
import os.path
import inspect

class config:
  # Locations
  experiments_dir = ''
  project_dir = ''
  protocol_dir = ''
  data_dir = ''

  # Behavior
  reset = True
  preserve = False

  # Storage
  storage = 'none' # mechanism name
  storage_server = '127.0.0.1' # if necessary

  # Parameters
  project_name = 'default'

  @classmethod
  def load(this_class, filename):
    contents = json.load(open(filename))
    for k in contents:
      if not hasattr(this_class,k):
        logging.warn('Parameter "'+k+'" is not a valid configuration option. Check your config file.')
      else:
        if inspect.ismethod(getattr(this_class,k)):
          logging.warn('Parameter "'+k+'" is not a valid configuration option (shadows a function). Check your config file.')
        else:
          setattr(this_class,k,contents[k])

  @classmethod
  def find(self, hint):
    # config file search priority:
    # 1. specified on the command line
    if hint is not None:
      if os.path.isfile(hint):
        logging.debug('Found config file at "'+hint+'"')
        return hint
    # 2. a 'protos.config' in the current directory
    if os.path.isfile('protos.config'):
      logging.debug('Found config file at "'+os.path.abspath('protos.config')+'"')
      return os.path.abspath('protos.config')
    # 3. a '.protos.config' in the user's home directory
    userfile = os.path.expanduser('~/.protos.config')
    if os.path.isfile(userfile):
      logging.debug('Found config file at "'+userfile+'"')
      return userfile
    # 4. the defaults set in this source file
    logging.warn('No config file found. Using defaults.')
    # This probably is not what you wanted.
    return None
