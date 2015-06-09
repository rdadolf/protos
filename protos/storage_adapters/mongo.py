import os
import os.path
from functools import reduce
import pwd
import logging
import pymongo
import ssl
import bson

from ..config import config
from ..internal import timestamp
from .adapters import Datastore, _json_subset

class Mongo(Datastore):
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
