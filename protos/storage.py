from .config import config
import logging
import json

class Datastore:
  def __init__(self):
    ''' Any storage initialization that needs to take place should happen here. Note that this function is called every time a bundle is read or written, so make sure that it *checks* expensive operations before blindly executing them.'''
    raise NotImplementedError
  def write(self, bundle):
    ''' This function should serialize the bundle and ship the .data, .metadata, and .files attributes to whatever backing store mechanism it uses. The bundle should be locatable via its .id attribute.'''
    raise NotImplementedError
  def read(self, bundle):
    ''' This function should use the bundle.id to find the bundle from the storage method it uses and populate the .data, .metadata, and .files attributes of this bundle.'''
    raise NotImplementedError

class Fake(Datastore):
  def __init__(self):
    pass
  def write(self, bundle):
    logging.debug('DATA: '+json.dumps(bundle.data))
    logging.debug('METADATA: '+json.dumps(bundle.metadata))
    logging.debug('FILES: '+json.dumps(bundle.files))
    pass
  def read(self, bundle):
    logging.debug('RETRIEVING:',bundle.id)
    pass

class MongoDB(Datastore):
  def __init__(self):
    pass
  def write(self, bundle):
    pass
  def read(self, bundle):
    pass

class Simple_Disk(Datastore):
  def __init__(self):

    '''
    #def _create_directory(self):
    if not os.path.isdir(self.directory):
      os.mkdir(self.directory)
    if os.path.isdir(self.directory) and config.reset:
      # FIXME: reset is too harsh, give finer granularity
      # Defensive programming
      assert len(self.directory)>1, 'empty bundle directory: '+str(self.directory)      shutil.rmtree(self.directory)
      os.mkdir(self.directory)
    '''

    pass
  def write(self, bundle):
    '''
    # FIXME: I just copy-pasted this so I don't lose the code. It does not work.

    # path is: os.path.join(self._experiment_path, self._name+'.bundle')
    self._create_dictionary()

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
      'xdata': self.xdata.serialize()
    }     
    json.dump( bundle_info, bundle_file, indent=2 )
    '''
    pass
  def read(self, bundle):
    pass

mechanisms = {
  'none' : Fake,
  'mongo' : MongoDB,
  'disk' : Simple_Disk
}

