import os
import os.path
from functools import reduce
import pwd
import re
import logging
import psycopg2 as pg

from ..config import config
from ..internal import timestamp
from .adapters import Datastore, _json_subset

# Psycopg 2.5 has something similar built-in, but several distro packages only
# have version 2.4. So we write our own.
class Transaction():
  def __init__(self, connection):
    self._conn = connection
    self._cur = None
  def __enter__(self):
    self._cur = self._conn.cursor()
    return self._cur # to the bound variable in the with block
  def __exit__(self, exc_type, exc_value, trace):
    if exc_type is None: # No error
      self._conn.commit()
      return True
    else: # Caught exception
      self._conn.rollback()
      return False # raise the exception 

def _sanitize(s):
  return re.sub(r'\W','',s)

class Postgres(Datastore):
  def __init__(self):
    self._conn = None
    self._connect()
    pass

  def _disconnect(self):
    if self._conn is not None:
      self._conn.close()
    self._conn = None

  def _connect(self):
    # Disconnect if necessary
    if self._conn is not None and self._conn.closed==0:
      self._conn.close()
      self._conn = None
    # Connect 
    username = pwd.getpwuid(os.getuid())[0]
    username = os.getenv('POSTGRES_USERNAME', username) # Allow the user to overrride the username used to connect to postgres

    logging.debug('Connecting to Postgres server on '+config.storage_server)
    self._conn = pg.connect(host=config.storage_server, database='protos', user=username)

  def _init_project_idempotently(self, project_name):
    sql='CREATE TABLE IF NOT EXISTS {0} (xid bigint, PRIMARY KEY (xid))'.format(_sanitize(project_name))
    args=[]
    with Transaction(self._conn) as X:
      X.execute(sql, args)
    pass

  def create_experiment_id(self, experiment_name):
    return '1' # FIXME

  def find_experiments(self, pattern):
    return ['1'] # FIXME

  def read_experiment_metadata(self, xid):
    return {} # FIXME

  def write_experiment_metadata(self, metadata, xid):
    return True # FIXME

  def find_bundles(self, pattern, xid):
    return [] # FIXME
 
  def write_bundle(self, bundle, xid):
    return True # FIXME
