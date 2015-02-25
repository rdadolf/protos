from .config import config
import os
import os.path
import logging
import json
import datetime

class Datastore:
  def __init__(self, experiment_name):
    ''' Any storage initialization that needs to take place should happen here. Note that this function is called every time a bundle is initialized, so make sure that it *checks* expensive operations before blindly executing them.'''
    raise NotImplementedError
  def write(self, bundle):
    ''' This function should take a serialized bundle and write it to whatever backing store it uses.'''
    raise NotImplementedError

class Fake(Datastore):
  def __init__(self, experiment_name):
    pass
  def write(self, bundle):
    logging.debug('DATA: '+json.dumps(bundle['data']))
    logging.debug('METADATA: '+json.dumps(bundle['metadata']))
    logging.debug('FILES: '+json.dumps(bundle['files']))
    pass

class MongoDB(Datastore):
  def __init__(self, experiment_name):
    pass
  def write(self, bundle):
    pass

class Simple_Disk(Datastore):
  def __init__(self, experiment_name):
    # Check/create the data directory
    if not os.path.isdir(config.data_dir):
      logging.warning('Data directory not found. Creating a new, empty one at "'+config.data_dir+'"') # This is unusual. Normally the data directory is already there. This might be a red flag for problems, but we can still carry on.
      os.mkdir(config.data_dir)
    # Check/create a project directory
    self._project_path = os.path.join(config.data_dir, config.project_name)
    if not os.path.isdir(self._project_path):
      os.mkdir(self._project_path)
    # Check/create an experiment directory
    self._exp_path = os.path.join(self._project_path, experiment_name+'_'+datetime.datetime.now().isoformat('_'))
    if not os.path.isdir(self._exp_path):
      os.mkdir(self._exp_path)

    # FIXME: I just copy-pasted this so I don't lose the code. It does not work.
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
    # FIXME: I just copy-pasted this so I don't lose the code. It does not work.
    '''
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

mechanisms = {
  'none' : Fake,
  'mongo' : MongoDB,
  'disk' : Simple_Disk
}

