
import logging
import tempfile
import os
import os.path
import shutil
import json
from functools import reduce

from .config import config

# These tokens are used at experiment parse time to thread data dependencies
# without having to invoke protocol functions (which are monadic and never
# actually executed until run time).
class Bundle_Token:
  def __init__(self,v=-1):
    self.v=v
  @property
  def id(self):
    return self.v
  def __repr__(self):
    return 'Bundle_Token('+str(self.id)+')'

class Token_Generator:
  bundle_id = 0 # must be integer

  @classmethod
  def new(self):
    rv = self.bundle_id
    self.bundle_id += 1
    return Bundle_Token(rv)

# This is the actual reference to the data that a protocol generates.
class Data_Bundle:
  def __init__(self, xdata, prefix='unnamed'):
    # Make sure we were passed an experiment data dictionary
    assert 'path' in xdata, 'Bundles must be passed experiment data when created'
    assert 'bundle_tag' in xdata, 'Bundles must be passed experiment data when created'

    self._prefix = prefix
    self._tag = xdata['bundle_tag']
    self._name = 'stage{number:03d}_{prefix}'.format( number=self._tag, prefix=self._prefix )

    # User-facing attributes
    self.xdata = xdata # dict
    self.metadata = dict()
    self.files = []
    self.directory = os.path.join(xdata['path'], self._name+'.bundle')

    # Setup
    self._create_directory()
    pass

  def __str__(self):
    return '<'+self._name+' data bundle>'

  def _set_id(self):
    self.tag

  def _create_directory(self):
    os.chdir(self.xdata['path'])

    if not os.path.isdir(self.directory):
      os.mkdir(self.directory)
    if os.path.isdir(self.directory) and config.reset:
      # FIXME: reset is too harsh, give finer granularity

      # Defensive programming
      assert len(self.directory)>1, 'empty bundle directory: '+str(self.directory)
      assert self.xdata['path'] in self.directory, 'errant bundle directory: '+str(self.directory)
      shutil.rmtree(self.directory)
      os.mkdir(self.directory)

  def _write_to_disk(self):
    logging.debug('Writing '+str(self)+' to disk')
    #logging.debug('Bundle list: '+str(self.files))
    # Check file list against actual directory contents
    d_contents = [os.path.join(self.directory,f) for f in os.listdir(self.directory)]
    #logging.debug('Actual list: '+str(d_contents))
    for f in self.files:
      assert f in d_contents, 'Missing file "'+f+'" in bundle '+str(self)
    # While it's not an error to have extra stuff in the bundle, it's not really
    # supposed to happen, so warn the user about it.
    for f in d_contents:
      if f not in d_contents:
        logging.warn('Untracked file "'+f+'" found in bundle '+str(self))

    # Serialize and write out metadata
    md_file = open( reduce(os.path.join, [self.directory, '._metadata']), 'w' )
    json.dump( self.metadata, md_file, indent=2 )

    # Serialize and write bundle info
    bundle_file = open( reduce(os.path.join, [self.directory, '._bundle']), 'w' )
    bundle_info = {
      'files': self.files,
      'directory': self.directory,
      'xdata': self.xdata
    }
    json.dump( bundle_info, bundle_file, indent=2 )

    return True

  def _read_from_disk(self):
    # FIXME
    # FIXME Check file list against actual directory contents
    # FIXME Check that the stored directory is the same as the actual one
    return False

  ### User methods ###

  def add_file(self, f):
    abs_f = os.path.abspath(f)
    assert os.path.isfile(abs_f), 'No file "'+str(abs_f)+'" to add to '+str(self._tag)
    shutil.copy(abs_f,self.directory)
    new_name = os.path.join( self.directory, os.path.basename(abs_f) )
    self.files.append(new_name)
