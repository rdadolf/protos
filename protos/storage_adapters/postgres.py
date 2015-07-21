import os
import os.path
import types
from functools import reduce
import pwd
import re
import logging
import psycopg2 as pg
import psycopg2.extras as extras

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
    self._cur = self._conn.cursor(cursor_factory=extras.DictCursor)
    return self._cur # to the bound variable in the with block
  def __exit__(self, exc_type, exc_value, trace):
    if exc_type is None: # No error
      self._conn.commit()
      return True
    else: # Caught exception
      self._conn.rollback()
      return False # raise the exception 

def _sanitize(s):
  # A little draconian, but ensures that nothing bad gets through.
  # (*only* variable-name-like characters are allowed)
  return re.sub(r'\W','',s)

class Postgres(Datastore):
  def __init__(self):
    self._conn = None
    self._connect()
    self._init_project_idempotently(config.project_name)
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
    assert self._conn.closed==0, 'Could not connect to server'

  def _ensure_connected(self):
    if self._conn is None or self._conn.close!=0:
      self._connect()

  def _init_project_idempotently(self, project_name):
    self._ensure_connected()
    sql='CREATE TABLE IF NOT EXISTS "{0}" ("xid" bigserial, PRIMARY KEY (xid), "id" varchar(256), "name" varchar(256), "host" varchar(256), "platform" varchar(256), "user" varchar(256))'.format(_sanitize(project_name))
    args=[]
    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(sql)+','+str(args))
      x.execute(sql, args)
    pass

  def create_experiment_id(self, experiment_name):
    self._ensure_connected()
    sql1 = 'INSERT INTO {0} ("name") VALUES (%s) RETURNING "xid"'.format(_sanitize(config.project_name))
    args1 = [experiment_name]
    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(sql1)+','+str(args1))
      x.execute(sql1,args1)
      xid = x.fetchone()['xid']
      # Need to do this atomically
      sql2 = 'UPDATE {0} SET "id"=%s WHERE "xid"=%s'.format(_sanitize(config.project_name))
      args2 = [xid,xid]
      logging.debug('PostgreSQL: '+str(sql2)+','+str(args2))
      x.execute(sql2,args2)
      return str(xid)

  def find_experiments(self, pattern):
    self._ensure_connected()
    # Check pattern is sane.
    if type(pattern)!=dict:
      logging.error('Malformed pattern specified while finding experiments')
      return []
    if pattern!={} and ( len(pattern)!=1 and 'metadata' not in pattern ):
      # FIXME: If we allow other criteria than metadata, update this test.
      logging.error('Invalid pattern: extraneous search fields')
      return []
    if pattern=={}:
      sql = 'SELECT "id" FROM {0}'.format(_sanitize(config.project_name))
      args = []
    else:
      if any([type(v)==dict or type(v)==list for (k,v) in pattern['metadata'].items()]):
        # Check for compound queries (disallowed)
        logging.error('Experiment queries are not allowed to have deeply-nested values')
        return []
      columns = ['"'+str(_sanitize(k))+'"' for k in pattern['metadata'].keys()]
      arg_str = ','.join([c+'=%s' for c in columns])
      sql = 'SELECT "id" FROM {0} WHERE {1}'.format(_sanitize(config.project_name), arg_str)
      args = pattern['metadata'].values()

    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+x.mogrify(sql,args))
      x.execute(sql,args)
      rs = x.fetchall()
      return [r['id'] for r in rs]

    logging.error('Experiment query failed')
    return []

  def read_experiment_metadata(self, xid):
    self._ensure_connected()
    sql = 'SELECT "id","name","host","platform","user" FROM {0} WHERE "xid"=%s'.format(_sanitize(config.project_name))
    args = xid
    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(sql)+','+str(args))
      x.execute(sql,args)
      r=x.fetchone() # xids are unique
      return dict(r)
    return {} # FIXME

  def write_experiment_metadata(self, metadata, xid):
    self._ensure_connected()
    return True # FIXME

  def find_bundles(self, pattern, xid):
    self._ensure_connected()
    return [] # FIXME
 
  def write_bundle(self, bundle, xid):
    self._ensure_connected()
    return True # FIXME
