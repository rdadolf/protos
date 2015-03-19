
import logging
from .config import config

from .storage import mechanisms as storage_mechanisms


class Query_Result:
  def __init__(self, datastore=None, xid=None):
    self._datastore = datastore
    self._xid = xid

  def metadata(self):
    return self._datastore.read_experiment_metadata(self._xid)

  def search_bundles(self,pattern):
    bundles = self._datastore.find_bundles(pattern, self._xid)
    return bundles


def search_experiments(pattern):
  assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
  datastore = storage_mechanisms[config.storage]()
  xids = datastore.find_experiments(pattern)
  return [Query_Result(datastore,xid) for xid in xids]
