import os
import os.path
import types
from functools import reduce
import pwd
import re
import logging
import json
import psycopg2 as pg
import psycopg2.extras as extras
from datetime import datetime

from ..config import config
from ..time import timestamp
from .adapters import Datastore, _json_subset

# Currently, everything is a strong.
# This is an odd choice, but not every storage adapter has the right types,
# so we go to the least common denominator.
EXP_METADATA_FIELDS=[
  ('id','varchar(256)'),
  ('name','varchar(256)'),
  ('host','varchar(256)'),
  ('platform','varchar(256)'),
  ('user','varchar(256)'),
  ('time','varchar(256)'),
  ('tags','varchar(1024)'),
  ('progress','varchar(10)'),
  ('last_error','varchar(256)')
]
BDL_METADATA_FIELDS=[
  ('id','varchar(256)'),
  ('bundle_type','varchar(256)'),
  ('time','varchar(256)'),
]

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
  def __init__(self, init=True):
    self._conn = None
    self._connect()
    if init:
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
    if self._conn is None or self._conn.closed!=0:
      self._connect()

  def _set_role_rw(self):
    self._ensure_connected()
    with Transaction(self._conn) as x:
      sql = 'SET ROLE rw_group'
      logging.debug('PostgreSQL: '+str(sql))
      x.execute(sql)
  def _set_role_ro(self):
    self._ensure_connected()
    with Transaction(self._conn) as x:
      sql = 'SET ROLE ro_group'
      logging.debug('PostgreSQL: '+str(sql))
      x.execute(sql)

  def _init_project_idempotently(self, project_name):
    self._ensure_connected()
    self._set_role_ro()
    xquery = "SELECT '{0}'::regclass".format(_sanitize(project_name))
    bquery = "SELECT '{0}_bundles'::regclass".format(_sanitize(project_name))
    need_new_xtable = False
    need_new_btable = False
    with Transaction(self._conn) as x:
      try:
        logging.debug('PostgreSQL: '+str(xquery))
        x.execute(xquery)
      except pg.ProgrammingError as e:
        need_new_xtable = True
    with Transaction(self._conn) as x:
      try:
        logging.debug('PostgreSQL: '+str(bquery))
        x.execute(bquery)
      except pg.ProgrammingError as e:
        need_new_btable = True

    try:
      self._set_role_rw()
    except pg.ProgrammingError as e:
      # Read-only user
      return

    # EXP TABLE
    self._set_role_rw()
    if need_new_xtable:
      columns = ', '.join(['"{0}" {1}'.format(col,typ) for (col,typ) in EXP_METADATA_FIELDS])
      xsql = 'CREATE TABLE "{0}" ("xid" bigserial, PRIMARY KEY ("xid"), {1})'.format(_sanitize(project_name), columns)
      with Transaction(self._conn) as x:
        logging.debug('PostgreSQL: '+str(xsql))
        x.execute(xsql)
    else: # Make sure all the columns are there.
      for (col,typ) in EXP_METADATA_FIELDS:
        xsql = 'ALTER TABLE "{0}" ADD COLUMN "{1}" {2}'.format(_sanitize(project_name), col, typ)
        with Transaction(self._conn) as x:
          logging.debug('PostgreSQL: '+str(xsql))
          try:
            x.execute(xsql)
          except pg.ProgrammingError as e:
            pass

    # BUNDLE TABLE
    if need_new_btable:
      columns = ', '.join(['"{0}" {1}'.format(col,typ) for (col,typ) in BDL_METADATA_FIELDS])
      bsql = 'CREATE TABLE "{0}_bundles" ("bid" bigserial, PRIMARY KEY ("bid"), "xid" bigint REFERENCES "{0}", {1}, "data" text, "files" text)'.format(_sanitize(project_name),  columns)
      with Transaction(self._conn) as x:
        logging.debug('PostgreSQL: '+str(bsql))
        x.execute(bsql)
    else: # Make sure all the columns are there.
      for (col,typ) in BDL_METADATA_FIELDS:
        xsql = 'ALTER TABLE "{0}_bundles" ADD COLUMN "{1}" {2}'.format(_sanitize(project_name), col, typ)
        with Transaction(self._conn) as x:
          logging.debug('PostgreSQL: '+str(xsql))
          try:
            x.execute(xsql)
          except pg.ProgrammingError as e:
            pass
  
  def create_experiment_id(self, experiment_name):
    self._ensure_connected()
    self._set_role_rw()
    sql1 = 'INSERT INTO "{0}" ("name") VALUES (%s) RETURNING "xid"'.format(_sanitize(config.project_name))
    args1 = [experiment_name]
    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(sql1)+','+str(args1))
      x.execute(sql1,args1)
      xid = x.fetchone()['xid']
      # Need to do this atomically
      sql2 = 'UPDATE "{0}" SET "id"=%s WHERE "xid"=%s'.format(_sanitize(config.project_name))
      args2 = [xid,xid]
      logging.debug('PostgreSQL: '+str(sql2)+','+str(args2))
      x.execute(sql2,args2)
      return str(xid)

  # FIXME: tag filters currently don't (really) work
  #   solution: allow non-equality filters (more than just "x=y")
  def find_experiments(self, pattern):
    self._ensure_connected()
    self._set_role_ro()
    # Check pattern is sane.
    if type(pattern)!=dict:
      logging.error('Malformed pattern specified while finding experiments')
      return []
    if pattern!={} and ( len(pattern)!=1 and 'metadata' not in pattern ):
      # FIXME: If we allow other criteria than metadata, update this test.
      logging.error('Invalid pattern: extraneous search fields')
      return []
    if pattern=={} or pattern['metadata']=={}:
      sql = 'SELECT "id" FROM "{0}"'.format(_sanitize(config.project_name))
      args = []
    else:
      if any([type(v)==dict or type(v)==list for (k,v) in pattern['metadata'].items()]):
        # Check for compound queries (disallowed)
        logging.error('Experiment queries are not allowed to have deeply-nested values')
        return []
      columns = ['"'+str(_sanitize(k))+'"' for k in pattern['metadata'].keys()]
      arg_str = ','.join([c+'=%s' for c in columns])
      sql = 'SELECT "id" FROM "{0}" WHERE {1}'.format(_sanitize(config.project_name), arg_str)
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
    self._set_role_ro()
    columns = ','.join(['"{0}"'.format(col) for (col,typ) in EXP_METADATA_FIELDS])
    sql = 'SELECT {0} FROM "{1}" WHERE "xid"=%s'.format(columns,_sanitize(config.project_name))
    args = [xid]
    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(sql)+','+str(args))
      x.execute(sql,args)
      r=x.fetchone() # xids are unique
      retval = dict(r)
      # FIXME: patch tags (this is a hack)
      logging.debug('RETVAL[tags]: '+str(type(retval['tags']))+','+str(retval['tags']))
      if retval['tags'] is not None and retval['tags']!='':
        retval['tags'] = json.loads(retval['tags'])
      else:
        retval['tags'] = []
      return retval
    logging.error('Couldnt read experiment metadata')
    return {}

  def write_experiment_metadata(self, metadata, xid):
    self._ensure_connected()
    self._set_role_rw()
    colnames = [col for (col,typ) in EXP_METADATA_FIELDS]
    mdnames = metadata.keys()
    # Only write valid MD values
    names = list(set(colnames)&set(mdnames))
    # If we try to write an MD field we don't know about, alert us to the problem
    if( len(names)<len(mdnames) ):
      logging.warning('Unknown metadata fields "'+str( set(mdnames)-set(colnames) )+'"')
    colsql = ','.join(['"{0}"'.format(n) for n in names])
    valsql = ','.join(['%s' for n in names])
    mdvalues = dict(metadata) # copy
    # FIXME: patch tags (this is a hack)
    if 'tags' in mdvalues:
      mdvalues['tags'] = json.dumps(mdvalues['tags'])
    values = [str(mdvalues[n]) for n in names]

    deconflict_sql = 'SELECT "xid" FROM "{0}" WHERE "xid"=%s'.format(_sanitize(config.project_name))
    deconflict_args = [xid]
    insert_sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(_sanitize(config.project_name), colsql, valsql)
    insert_args= values
    update_sql = 'UPDATE "{0}" SET ({1}) = ({2}) WHERE "xid"=%s'.format(_sanitize(config.project_name), colsql, valsql)
    update_args=values+[xid]

    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+x.mogrify(deconflict_sql,deconflict_args))
      x.execute(deconflict_sql, deconflict_args)
      r=x.fetchall()
      if len(r)==0:
        logging.debug('PostgreSQL: '+x.mogrify(insert_sql,insert_args))
        x.execute(insert_sql,insert_args)
      else:
        logging.debug('PostgreSQL: '+x.mogrify(update_sql,update_args))
        x.execute(update_sql,update_args)
    return True

  def find_bundles(self, pattern, xid):
    self._ensure_connected()
    self._set_role_ro()

    md = {}
    if 'metadata' in pattern:
      md = pattern['metadata']
    dat = {}
    if 'data' in pattern:
      dat = pattern['data']
    # FIXME: ignores files

    colnames = [col for (col,typ) in BDL_METADATA_FIELDS]
    mdnames = md.keys()
    # Only match valid MD values
    names = list(set(colnames)&set(mdnames))
    # If we try to write an MD field we don't know about, alert us to the problem
    if( len(names)<len(mdnames) ):
      logging.warning('Unknown metadata fields "'+str( set(mdnames)-set(colnames) )+'"')
    constraints = ['"xid"=%s']
    constraints += ' AND '.join(['"{0}"=%s'.format(n) for n in names])
    values = [xid]
    values += [md[n] for n in names]

    with Transaction(self._conn) as x:
      qsql = 'SELECT * FROM "{0}_bundles" WHERE xid=%s'.format(_sanitize(config.project_name))
      qsql_args = [xid]
      x.execute(qsql, qsql_args)
      bs = x.fetchall()
      bundles = [{'metadata': {k:j[k] for (k,t) in BDL_METADATA_FIELDS}, 'data':json.loads(j['data'])} for j in bs]
      return [b for b in bundles if _json_subset(dat,b)]
    logging.error('Failed to find bundles')
    return []

 
  def write_bundle(self, bundle, xid):
    self._ensure_connected()
    self._set_role_rw()

    bundle['metadata']['id'] = 0 # placeholder, will get replaced with bid (we just don't expect the user to remember to specify a dummy value
    columns = [col for (col,typ) in BDL_METADATA_FIELDS]
    colsql = ','.join(['"{0}"'.format(c) for c in columns])
    values = [bundle['metadata'][c] for c in columns]
    valsql = ','.join(['%s' for c in columns])
    qsql = 'INSERT INTO "{0}_bundles" ("xid", {1}, "data", "files") VALUES (%s,{2},%s,%s) RETURNING "bid"'.format(_sanitize(config.project_name), colsql, valsql)
    qsql_args = [xid]+values+[json.dumps(bundle['data'])]+[json.dumps(bundle['files'])]
    bsql = 'UPDATE "{0}_bundles" SET "id"=%s WHERE "bid"=%s'.format(_sanitize(config.project_name))

    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+str(qsql))
      x.execute(qsql,qsql_args)
      bid = x.fetchone()['bid']
      bsql_args = [bid,bid]
      logging.debug('PostgreSQL: '+str(bsql))
      x.execute(bsql,bsql_args)

    return bid

  def delete_experiment(self, xid):
    self._ensure_connected()
    self._set_role_rw()

    bsql = 'DELETE FROM "{0}_bundles" WHERE "xid"=%s'.format(_sanitize(config.project_name))
    bsql_args = [str(xid)]
    xsql = 'DELETE FROM "{0}" WHERE "xid"=%s'.format(_sanitize(config.project_name))
    xsql_args = [str(xid)]

    with Transaction(self._conn) as x:
      logging.debug('PostgreSQL: '+x.mogrify(bsql,bsql_args))
      x.execute(bsql, bsql_args)
      logging.debug('PostgreSQL: '+x.mogrify(xsql,xsql_args))
      x.execute(xsql, xsql_args)

    return True
