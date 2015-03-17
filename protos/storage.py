from .config import config
import os
import os.path
from functools import reduce
import pwd
import logging
import json
import datetime
import pymongo

class Datastore: # Abstract interface class
  def __init__(self):
    ''' Any storage initialization that needs to take place should happen here. Note that this function is called *at least* every time a bundle is initialized, so make sure that it *checks* expensive operations before blindly executing them.'''
    raise NotImplementedError
  def create_experiment_id(self, experiment_name):
    ''' This function should take experiment info and create a space for it on the datastore. It should return a unique identifier which can be reused for write_bundle. Calling it twice will create two different experiment ids.'''
    raise NotImplementedError

  def update_experiment_metadata(self, metadata, xid):
    ''' This should take a JSON dictionary of metadata and write it to the datastore, associated with the experiment as a whole. Bundles have their own metadata which is handled separately.'''
    raise NonImplementedError

  def write_bundle(self, bundle, xid):
    ''' This function should take a serialized bundle and write it to whatever backing store it uses.'''
    raise NotImplementedError

class Fake(Datastore):
  def __init__(self):
    pass
  def create_experiment_id(self, experiment_name):
    logging.debug('EXP: '+experiment_name)
    pass
  def update_experiment_metadata(self, metadata, xid):
    logging.debug('EXP-METADATA: '+json.dumps(metadata))
  def write_bundle(self, bundle, xid):
    logging.debug('DATA: '+json.dumps(bundle['data']))
    logging.debug('METADATA: '+json.dumps(bundle['metadata']))
    logging.debug('FILES: '+json.dumps(bundle['files']))
    pass

class MongoDB(Datastore):
  def __init__(self):
    self._clean_connection_state()
    self._reconnect()

  def _clean_connection_state(self):
    self._conn = None
    self._db = None
    self._proj = None

  def _reconnect(self):
    # Disconnect if necessary
    if self._conn:
      if self._conn.alive():
        return True
      else:
        self._conn.close()
        self._clean_connection_state()
    # Connect
    username = pwd.getpwuid(os.getuid())[0]
    # FIXME: Make PEMfile path configurable
    pemfile = reduce(os.path.join, [os.getenv('HOME','/etc'), '.ssl', username+'.pem'])
    logging.debug('Connecting to MongoDB server on '+config.storage_server)
    self._conn = pymongo.MongoClient(config.storage_server, ssl=True, ssl_certfile=pemfile)
    if not self._conn.alive():
      logging.error('Could not connect to databse')
    self._db = self._conn['protos']
    # Authenticate
    mongoname = 'CN='+username+',OU=ACC,O=Harvard,L=Cambridge,ST=Massachusetts,C=US'
    self._db.authenticate(name=mongoname, mechanism='MONGODB-X509')
    # Set database write concern to 'authenticate'
    #   We have no replicas, so don't wait for any
    #   Don't wait for journaling. We'll trust it in the name of performance.
    self._db.write_concern = {'w':1}
    # Find/create project collection
    if config.project_name not in self._db.collection_names():
      self._db.create_collection(name=config.project_name)
      assert config.project_name in self._db.collection_names(), 'Failed to create a new project collection in database for "'+config.project_name+'"'
    self._proj = self._db[config.project_name]

  def create_experiment_id(self, experiment_name):
    experiment = { 'name': experiment_name, 'metadata': {}, 'bundles': [] }
    # Note: this need not be unique. The '_id' attribute will be automatically 
    # created and unique. If you run the same experiment twice, two documents
    # will be created, each with the same 'name' attribute. The way to
    # disambiguate between them is through querying differing attributes. The
    # '_id' returned from that query can be used to reference it uniquely.
    id = self._proj.insert(experiment)
    return id

  def update_experiment_metadata(self, metadata, xid):
    # Since there's only one metadata doc (or should be), we can update directly.
    new_md = self._proj.update( {'_id':xid}, {'$set': {'metadata': metadata}} )
    logging.debug('Wrote new experiment metadata:\n'+str(new_md))
    return True
 
  def write_bundle(self, bundle, xid):
    self._reconnect()
    bundle_id = self._proj.update( {'_id':xid}, {'$push': {'bundles': bundle}} )
    return True

class Simple_Disk(Datastore):
  def __init__(self):
    self._project_path = None

    # Check/create the data directory
    if not os.path.isdir(config.data_dir):
      logging.warning('Data directory not found. Creating a new, empty one at "'+config.data_dir+'"') # This is unusual. Normally the data directory is already there. This might be a red flag for problems, but we can still carry on.
      os.mkdir(config.data_dir)
    # Check/create a project directory
    self._project_path = os.path.join(config.data_dir, config.project_name)
    if not os.path.isdir(self._project_path):
      os.mkdir(self._project_path)

  def create_experiment_id(self, experiment_name):
    # Check/create an experiment directory
    exp_path = os.path.join(self._project_path, experiment_name+'_'+datetime.datetime.now().isoformat('_'))
    if not os.path.isdir(exp_path):
      os.mkdir(exp_path)
    # XID is the path to the experiment directory
    return exp_path

  def update_experiment_metadata(self, metadata, xid):
    # XID is the path to the experiment directory
    # FYI: Blows away previous metadata, even if it had more information.
    f = open(os.path.join(xid, 'metadata'), 'w')
    logging.debug('Writing experiment metadata to disk:\n'+json.dumps(metadata,indent=2))
    json.dump(metadata,f,indent=2)

  def write_bundle(self, bundle, xid):
    assert 'metadata' in bundle, 'Data bundle corrupted? No metadata found.'
    assert 'id' in bundle['metadata'], 'Data bundle corrupted? No ID in metadata.'
    bundle_id = bundle['metadata']['id']

    # XID is the path to the experiment directory
    f = open(os.path.join(xid, bundle_id), 'w')
    logging.debug('Writing data bundle to disk:\n'+json.dumps(bundle,indent=2))
    json.dump(bundle,f,indent=2)

mechanisms = {
  'none' : Fake,
  'mongo' : MongoDB,
  'disk' : Simple_Disk
}

