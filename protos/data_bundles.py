
import logging
import tempfile
import os
import os.path
import shutil
import uuid
from functools import reduce

from .config import config

from .storage import Fake, GCloud, Simple_Disk
storage_methods = {
  'fake' : Fake,
  'gcloud' : GCloud,
  'disk' : Simple_Disk,
}

# FIXME? This interface between Experiments and Bundles seems clunky.
class Experiment_Data:
  #def __init__(self, path, bundle_tag): # FIXME: remove
  def __init__(self, bundle_tag):
    #self.path = path # FIXME: remove
    self.bundle_tag = bundle_tag
  def serialize(self):
    # dictionary with __init__ kwargs as keys
    # This should work:
    #   xdata == Experiment_Data(**(xdata.serialize()))
    return { 'bundle_tag': self.bundle_tag }
    #return { 'path': self.path, 'bundle_tag': self.bundle_tag } # FIXME: remove

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
  def __init__(self, xdata, name='unnamed', _no_init=False):
    # It's an easy mistake to forget the xdata argument, since the users just
    # pass it in blindly, without really knowing why or what it is. If they
    # forget but still add a name, it could get picked up as the first argument.
    assert isinstance(xdata, Experiment_Data), 'Bundles must be passed experiment data when created'

    self._tag = xdata.bundle_tag
    self._name = name

    # When reading in a cached bundle, protos still creates a bundle object and
    # calls the _read() method. In this case, all the initialization will just
    # be overwritten anyways, so it is skipped.
    if not _no_init:
      # User-facing attributes
      self.metadata = dict()
      self.data = dict()
      self.files = []

      # Create a globally unique identifier on creation.
      self.metadata['id'] = uuid.uuid1(clock_seq=self._tag).hex

  @property
  def id(self):
    return self.metadata['id']

  def __repr__(self):
    return '<'+self._name+' data bundle>'

  def _write(self):
    ''' Persistently stores a copy of the bundle for archiving and/or reuse. '''
    assert config.storage in storage_methods, 'Could not find data storage adapter "'+config.storage+'"'
    Mechanism = storage_methods[config.storage]
    m = Mechanism()
    m.write(self)
    return True

  def _read(self):
    ''' Populates the bundle with a pre-computed (cached) version.'''
    assert config.storage in storage_methods, 'Could not find data storage adapter "'+config.storage+'"'
    Mechanism = storage_methods[config.storage]
    m = Mechanism()
    m.read(self)
    return self

  ### User-facing ###

  def add_file(self, f):
    abs_f = os.path.abspath(f)
    assert os.path.isfile(abs_f), 'No file "'+str(abs_f)+'" to add to '+str(self)
    shutil.copy(abs_f,self.directory)
    new_name = os.path.join( self.directory, os.path.basename(abs_f) )
    self.files.append(new_name)
