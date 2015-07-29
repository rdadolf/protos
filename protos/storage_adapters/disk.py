import os
import os.path
from functools import reduce
import pwd
import logging
import json
import shutil

from ..config import config
from ..time import timestamp
from .adapters import Datastore, _json_subset

class Disk(Datastore):
  def __init__(self):
    self._project_path = None

    # Check/create the data directory if necessary
    if not os.path.isdir(config.data_dir):
      assert config.data_dir!='', 'Config parameter "data_dir" cannot be empty if using the "disk" storage adapter'
      logging.warning('Data directory not found. Creating a new, empty one at "'+config.data_dir+'"') # This is unusual. Normally the data directory is already there. This might be a red flag for problems, but we can still carry on.
      os.mkdir(config.data_dir)
    # Check/create a project directory
    self._project_path = os.path.join(config.data_dir, config.project_name)
    if not os.path.isdir(self._project_path):
      os.mkdir(self._project_path)

  def create_experiment_id(self, experiment_name):
    # This is probably good enough to be unique. Don't run 1B parallel copies.
    xid = experiment_name+'_'+timestamp()
    # Check/create an experiment directory
    xpath = self._get_xpath(xid)
    if not os.path.isdir(xpath):
      os.mkdir(xpath)
    return xid

  def _get_xpath(self, xid):
    xpath = os.path.join(self._project_path, xid)
    return xpath

  def find_experiments(self, pattern):
    project_dir = os.path.join(config.data_dir, config.project_name)
    possible_experiments = os.listdir(project_dir)
    found_experiments = []
    for xdir in possible_experiments:
      mdfile = reduce(os.path.join, [project_dir, xdir, 'metadata'])
      if not os.path.isfile(mdfile):
        continue # Someone's polluted the data directory
      exp = {'metadata':json.load(open(mdfile,'r'))}
      assert 'id' in exp['metadata'], 'Corrupted experiment metadata file'
      if _json_subset(pattern, exp):
        xid = exp['metadata']['id']
        found_experiments.append(xid)
    return found_experiments

  def read_experiment_metadata(self, xid):
    metapath = os.path.join(self._get_xpath(xid), 'metadata')
    metadata = json.load(open(metapath,'r'))
    assert 'id' in metadata, 'Experiment metadata file is corrupted'
    return metadata

  def write_experiment_metadata(self, metadata, xid):
    # XID is the path to the experiment directory
    # FYI: Blows away previous metadata, even if it had more information.
    metapath = os.path.join(self._get_xpath(xid), 'metadata')
    f = open(metapath,'w')
    logging.debug('Writing experiment metadata to disk:\n'+json.dumps(metadata,indent=2))
    json.dump(metadata,f,indent=2)

  def find_bundles(self, pattern, xid):
    xpath = self._get_xpath(xid)
    fnames = os.listdir(xpath)
    assert 'metadata' in fnames, 'Bad experiment id: '+str(xid)+' (no metadata)'
    fnames.remove('metadata')
    candidates = [json.load(open(os.path.join(xpath,f),'r')) for f in fnames]
    return [b for b in candidates if _json_subset(pattern,b)]

  def write_bundle(self, bundle, xid):
    assert 'metadata' in bundle, 'Data bundle corrupted? No metadata found.'
    assert 'id' in bundle['metadata'], 'Data bundle corrupted? No ID in metadata.'
    bundle_id = bundle['metadata']['id']

    f = open(os.path.join(self._get_xpath(xid), bundle_id), 'w')
    logging.debug('Writing data bundle to disk:\n'+json.dumps(bundle,indent=2))
    json.dump(bundle,f,indent=2)


  def delete_experiment(self, xid):
    xpath = self._get_xpath(xid)
    assert os.path.isdir(xpath), 'Experiment does not exist'
    shutil.rmtree(xpath)
    if os.path.isdir(xpath):
      logging.error('Failed to delete experiment '+str(xid)+' at '+str(xpath))
      return False
    return True
