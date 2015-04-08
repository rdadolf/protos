
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

  def exact_bundles(self, id):
    # FIXME: NYI
    return None


def search_experiments(pattern):
  assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
  datastore = storage_mechanisms[config.storage]()
  xids = datastore.find_experiments(pattern)
  return [Query_Result(datastore,xid) for xid in xids]

def exact_experiment(xid):
  # We could create a query result directly, but let's actually query to verify
  # that the xid exists.
  assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
  datastore = storage_mechanisms[config.storage]()
  xids = datastore.find_experiments({'metadata':{'id',xid}})
  if len(xids)!=1:
    logging.warning('No experiment found with id "'+str(xid)+'"')
    return None
  return Query_Result(datastore,xids[0])
