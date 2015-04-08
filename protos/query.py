
import logging
from .config import config

from .storage import mechanisms as storage_mechanisms


class Query_Result:
  def __init__(self, datastore=None, xid=None):
    self._datastore = datastore
    self._xid = xid

  @property
  def id(self):
    return str(self._xid)

  def metadata(self):
    return self._datastore.read_experiment_metadata(self._xid)

  def search_bundles(self,pattern):
    bundles = self._datastore.find_bundles(pattern, self._xid)
    return bundles

  def exact_bundle(self,bid):
    bundles = self._datastore.find_bundles({'metadata':{'id':str(bid)}}, self._xid)
    if len(bundles)==0:
      logging.debug('No bundle id matched "'+str(bid)+'"')
      return None
    if len(bundles)>1:
      logging.error('Non-unique bundle id detected: "'+str(bid)+'"')
      # This should never happen, so if it does, something has gone horribly
      # wrong and we probably can't trust any of the results. 
      return None
    return bundles[0]


def search_experiments(pattern):
  assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
  datastore = storage_mechanisms[config.storage]()
  xids = list(datastore.find_experiments(pattern))
  return [Query_Result(datastore,xid) for xid in xids]

def exact_experiment(xid):
  assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
  datastore = storage_mechanisms[config.storage]()
  xids = list(datastore.find_experiments({'metadata':{'id':str(xid)}}))
  if len(xids)==0:
    logging.debug('No experiment id matched "'+str(xid)+'"')
    return None
  if len(xids)>1:
    logging.error('Non-unique experiment id detected: "'+str(xid)+'"')
    # This should never happen, so if it does, something has gone horribly
    # wrong and we probably can't trust any of the results. 
    return None
  return Query_Result(datastore,xids[0])
