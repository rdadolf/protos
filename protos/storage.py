from .config import config
import os
import os.path
from functools import reduce
import pwd
import logging
import json
import pymongo
import ssl
import bson

from .internal import timestamp

def _json_subset(pat,data,indent=0):
  if (type(data) is list) and (type(pat) is list):
    #print ' '*indent,'LIST:'#,pat,data
    for subpat in pat:
      if not any([_json_subset(subpat,subdata,indent+2) for subdata in data]):
        #print ' '*indent,'FAILED LIST'
        return None

  elif (type(data) is dict) and (type(pat) is dict):
    #print ' '*indent,'DICT:',pat.keys(),data.keys()
    if not all([pat_k in data.keys() for (pat_k,pat_v) in pat.items()]):
      #print ' '*indent,'FAILED DICT (KEY)'
      return None
    arry=[_json_subset(pat_v,data[pat_k],indent+2) for (pat_k,pat_v) in pat.items()]
    #if not all([_json_subset(pat_v,data[pat_k],indent+2) for (pat_k,pat_v) in pat.items()]):
    if not all(arry):
      #print ' '*indent,'FAILED DICT (VALUE)'
      return None

  else: # scalar
    #print ' '*indent,'SCALAR:',pat,data
    if pat!=data:
      #print ' '*indent,'FAILED SCALAR'
      return None

  #print ' '*indent,'PASSED'
  return data

class Datastore: # Abstract interface class
  def __init__(self):
    ''' Any storage initialization that needs to take place should happen here. Note that this function is called *at least* every time a bundle is initialized, so make sure that it *checks* expensive operations before blindly executing them.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def create_experiment_id(self, experiment_name):
    ''' This function should take experiment info and create a space for it on the datastore. It should return a unique identifier which can be reused for write_bundle. Calling it twice will create two different experiment ids.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def find_experiments(self, pattern):
    '''Returns a list of xid's for experiments that match the pattern given.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def read_experiment_metadata(self, xid):
    '''Returns a JSON dictionary of metadata.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def write_experiment_metadata(self, metadata, xid):
    ''' This should take a JSON dictionary of metadata and write it to the datastore, associated with the experiment as a whole. Bundles have their own metadata which is handled separately.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def find_bundles(self, pattern, xid):
    ''' Returns a list of data bundle objects.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def write_bundle(self, bundle, xid):
    ''' This function should take a serialized bundle and write it to whatever backing store it uses.'''
    raise NotImplementedError('Missing implementation in storage adapter')

class Fake(Datastore):
  def __init__(self):
    pass
  def create_experiment_id(self, experiment_name):
    logging.debug('NEW EXP ID: 5')
    return '5'
  def find_experiments(self,pattern):
    logging.debug('FIND EXPS: '+str(pattern))
    return []
  def read_experiment_metadata(self, xid):
    logging.debug('READ EXP-METADATA: '+str(xid))
    return {}
  def write_experiment_metadata(self, metadata, xid):
    logging.debug('WRITE EXP-METADATA: '+json.dumps(metadata))
  def find_bundles(self, pattern, xid):
    logging.debug('FIND BUNDLES: '+str(pattern))
    return []
  def write_bundle(self, bundle, xid):
    logging.debug('BUNDLE:')
    logging.debug('DATA: '+json.dumps(bundle['data']))
    logging.debug('METADATA: '+json.dumps(bundle['metadata']))
    logging.debug('FILES: '+json.dumps(bundle['files']))

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
      try:
        self._conn.server_info()
        return True
      except:
        self._conn.close()
        self._conn = None # mongo will resurrect this connection if used again
        self._clean_connection_state()
      # Exception caught and handled. Now we need a new connection.
    # Connect
    username = pwd.getpwuid(os.getuid())[0]
    username = os.getenv('MONGO_USERNAME', username) # Allow the user to override the username used to connect to mongodb (and the ssl file)
    # FIXME: Make PEMfile path configurable
    pemfile = reduce(os.path.join, [os.getenv('HOME','/etc'), '.ssl', username+'.pem'])
    logging.debug('Connecting to MongoDB server on '+config.storage_server)
    # FIXME: CERT_NONE means we don't authenticate the server from the client. However, it also means that we don't need to distribute server certificates to all the clients. It's not hard, but currently we have a hostname mismatch on the rootCA cert on our server, so it won't authenticate. Summary: clients are hoping they're not man-in-the-middle'd while contacting a server.
    self._conn = pymongo.MongoClient(config.storage_server, ssl=True, ssl_certfile=pemfile, ssl_cert_reqs=ssl.CERT_NONE)
    self._db = self._conn['protos']
    # Authenticate
    mongoname = 'CN='+username+',OU=ACC,O=Harvard,L=Cambridge,ST=Massachusetts,C=US'
    self._db.authenticate(name=mongoname, mechanism='MONGODB-X509')

    # Set database write concern to 'acknowledge'
    #   We have no replicas, so don't wait for any
    #   Don't wait for journaling. We'll trust it in the name of performance.
    #self._db.write_concern = {'w':1}
    # FIXME: pymongo 3.0 broke this. Luckily, 'acknowledge' is already the
    # default write concern for mongodb, so we'll just remove the explicit
    # call. Beware if this changes in the future.

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
    # Note: Don't do anything to the metadata behind the scenes here, since it
    # will be overwritten by any call to write_experiment_metadata().
    # Experiment objects are the primary owners and controllers of metadata,
    # not storage adapters. (This is to simplify consistent behavior across
    # adapters.)
    return id

  def _pattern_to_query(self, pattern, prefix=None):
    if prefix is not None:
      prefix += '.'
    else:
      prefix = ''
    d = {}
    for (p,v) in pattern.items():
      if type(v) is dict:
        d.update( self._pattern_to_query(v,prefix=prefix+p) )
      elif type(v) is list:
        # FIXME: How do I handle lists?
        assert False, 'Not Implemented Yet'
      else:
        d[prefix+p] = v 
    return d

  def find_experiments(self, pattern):
    query = self._pattern_to_query(pattern)
    projection = {}
    results = self._proj.find(query,projection) # returns Cursor object
    return [str(result['_id']) for result in results]

  def read_experiment_metadata(self, xid):
    query = {'_id': bson.objectid.ObjectId(xid)}
    projection = {'_id': 0, 'metadata': 1}
    md = self._proj.find(query, projection)
    if md.count()==0:
      logging.warning('Couldnt read metadata from experiment'+str(xid)+'"')
      return {}
    return md[0]['metadata']

  def write_experiment_metadata(self, metadata, xid):
    # Since there's only one metadata doc (or should be), we can update directly.
    new_md = self._proj.update( {'_id':bson.objectid.ObjectId(xid)}, {'$set': {'metadata': metadata}} )
    logging.debug('Wrote new experiment metadata:\n'+str(new_md))
    return True

  def find_bundles(self, pattern, xid):
    # I can't find a good native way to do this in MongoDB, given that bundles
    # are implemented as subdocuments.

    # Grab all of the bundles from the specified experiment
    agg_results = self._proj.aggregate([
        {'$match': { '_id': bson.objectid.ObjectId(xid) }},
        {'$unwind': '$bundles'},
        {'$project': {'bundles': 1}}],
      cursor={}) # returns a CommandCursor, which can be iterated over for results

    # FIXME
    bundles = [r['bundles'] for r in agg_results]
    # Filter and return
    return [b for b in bundles if _json_subset(pattern,b)]
 
  def write_bundle(self, bundle, xid):
    self._reconnect()
    bundle_id = self._proj.update( {'_id':bson.objectid.ObjectId(xid)}, {'$push': {'bundles': bundle}} )
    return True

class Simple_Disk(Datastore):
  def __init__(self):
    self._project_path = None

    # Check/create the data directory if necessary
    if not os.path.isdir(config.data_dir):
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

mechanisms = {
  'none' : Fake,
  'mongo' : MongoDB,
  'disk' : Simple_Disk
}

