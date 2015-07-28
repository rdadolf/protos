
import logging
import tempfile
import os
import os.path
import shutil
import uuid
from functools import reduce

from .config import config
from .internal import timestamp

# Experiment data is strictly a data packaging mechanism for transferring
# information about the experiment in progress to the data bundles it uses.
# This class could be replaced with a tuple, but having a class identity is
# useful for error checking.
# FIXME? This interface between Experiments and Bundles seems clunky.
class Experiment_Data:
  def __init__(self, bundle_tag, storage, storage_xid, xscratch):
    self.bundle_tag = bundle_tag
    self.storage = storage
    self.storage_xid = storage_xid
    self.xscratch = xscratch
  @property
  def directory(self):
    '''
A directory that persists for the life of the experiment.

Protocols can use this directory in one of two ways:
1) Manually move files to this directory, then call bundle.add_file(<path>).
2) Call bundle.add_file(<path>, copy=True)
'''
    return self.xscratch

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
  def __init__(self, xdata, name='unnamed', _init=None):
    # It's an easy mistake to forget the xdata argument, since the users just
    # pass it in blindly, without really knowing why or what it is. If they
    # forget but still add a name, it could get picked up as the first argument.
    assert isinstance(xdata, Experiment_Data), 'Bundles must be passed experiment data when created'

    self._name = name
    self._tag = xdata.bundle_tag
    self._storage = xdata.storage
    self._storage_xid = xdata.storage_xid
    self._xscratch = xdata.directory

    # When protos creates a bundle from precomputed data, it uses all of the
    # fields from the old bundle, so there's no reason to initialize anything.
    if _init is None:
      # User-facing attributes
      self.metadata = dict()
      self.data = dict()
      self.files = []
      # Create a globally unique identifier on creation.
      self.metadata['id'] = uuid.uuid1(clock_seq=self._tag).hex
      self.metadata['bundle_type'] = self._name
      self.metadata['time'] = timestamp()
      # FIXME: needs more metadata
    else: # _init is a previously-externalized JSON object
      self._internalize(_init)

  @property
  def id(self):
    return self.metadata['id']

  def __repr__(self):
    return '<'+self._name+' data bundle>'

  def _internalize(self, json_dict):
    self.data = json_dict['data']
    self.metadata = json_dict['metadata']
    self.files = json_dict['files']
    # We record our name in two places. This is the second one.
    self._name = self.metadata['bundle_type']

  def _externalize(self):
    # NOTE: we *assume* that the metadata and data dictionaries are safe to
    #   represent in JSON. This is not guaranteed, since users can augment
    #   data bundles with whatever they want. I don't know a good way to check
    #   this, but there's a concern that it could corrupt data output if it
    #   isn't done.
    s = dict()
    s['data'] = self.data
    s['metadata'] = self.metadata
    s['files'] = self.files
    return s

  def _persist(self):
    ''' Persistently stores a copy of the bundle for archiving and/or reuse. '''
    self._storage.write_bundle( self._externalize(), self._storage_xid )
    return True

  ### User-facing ###

  def add_file(self, f, copy=False):
    abs_f = os.path.abspath(f)
    assert os.path.isfile(abs_f), 'No file "'+str(abs_f)+'" to add to '+str(self)
    assert os.path.isdir(self._xscratch), 'Corrupted experiment state: experiment scratch directory "'+str(self._xscratch)+'" doesnt exist'

    if copy:
      shutil.copy(abs_f, self._xscratch)
      name = os.path.join( self._xscratch, os.path.basename(abs_f) )
    else:
      name = abs_f

    self.files.append(name)


class Void_Bundle(Data_Bundle):
  def __init__(self, experiment):
    Data_Bundle.__init__(self, experiment, name='void')
