from utils import *
import os
import json
import nose
from psycopg2 import OperationalError

STORAGE_SERVER=os.getenv('PROTOS_STORAGE_SERVER', '127.0.0.1')

@set_config(storage='postgres')
def test_sanitize():
  sani = protos.storage_adapters.postgres._sanitize
  cases = [
    ('foo \r\nbar', 'foobar', 'Whitespace not removed'),
    ('foo!@#$%^&*()bar', 'foobar', 'Special characters not removed'),
    ('foo\'"bar', 'foobar', 'Quotes not removed'),
  ]
  for (lhs,rhs,why) in cases:
    assert sani(lhs)==rhs, why

# Auto-cleanup for test database tables
class ProjectDB():
  def __init__(self):
    pass
  def __enter__(self):
    try:
      protos.storage_adapters.postgres.Postgres(init=False)
    except OperationalError as e:
      raise nose.SkipTest
    self.pg = protos.storage_adapters.postgres.Postgres(init=False)
    return self.pg
  def __exit__(self, exc_type, exc_value, trace):
    self.pg._set_role_rw()
    with protos.storage_adapters.postgres.Transaction(self.pg._conn) as x:
      x.execute('DROP TABLE IF EXISTS test_project CASCADE')
      x.execute('DROP TABLE IF EXISTS test_project_bundles CASCADE')

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_authentication():
  with ProjectDB() as pg:
    assert pg._conn.closed==0, 'Connection failed'
  

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_init():
  with ProjectDB() as pg:
    with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
      x.execute('SELECT xid FROM "test_project" WHERE false')
      x.execute('SELECT xid FROM "test_project_bundles" WHERE false')
      # We don't care about the result. Just testing whether the table exists.

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_xid():
  with ProjectDB() as pg:
    xid = pg.create_experiment_id('x1')
    with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
      x.execute('SELECT * FROM test_project;')
      r = x.fetchall()
      assert len(r)==1, 'Incorrect number of results.'

    xid = pg.create_experiment_id('x2')
    with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
      x.execute('SELECT * FROM test_project;')
      r = x.fetchall()
      assert len(r)==2, 'Incorrect number of results.'

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_experiment_metadata():
  with ProjectDB() as pg:
    xid = pg.create_experiment_id('x1')
    md = pg.read_experiment_metadata(xid)
    assert type(md)==type({}), 'Incorrect return type for experiment metadata'
    assert ('id' in md) and (type(md['id'])==str), 'xid not converted to string id in experiment metadata output'
  
    # Test with a full MD
    md = {'id': xid,
          'name': 'example',
          'host': 'localhost',
          'platform': '*nix',
          'user': 'me',
          'time': '2015-07-22_14-38-11-522354_UTC',
          'tags': ['tag1','tag2'],
          'progress': '60' }
    pg.write_experiment_metadata(md, xid)
    md_back = pg.read_experiment_metadata(xid)
    for (k1,v1) in md.items():
      assert v1==md_back[k1], 'Incorrect key: '+str(k1)+' ('+v1+','+md_back[k1]+')'

    # Test with an empty MD
    md = {'id': xid}
    pg.write_experiment_metadata(md, xid)
    md_back = pg.read_experiment_metadata(xid)
    for (k1,v1) in md.items():
      assert v1==md_back[k1], 'Incorrect key: '+str(k1)+' ('+v1+','+md_back[k1]+')'

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_find_experiment():
  with ProjectDB() as pg:
    x1 = pg.create_experiment_id('x1')
    x2 = pg.create_experiment_id('x2')
    q1 = {'metadata': {'id':x1}}
    q2 = {'metadata': {'id':'1234'}}
  
    xids = pg.find_experiments(q1)
    assert len(xids)==1, 'Couldnt find the right experiments'
    md = pg.read_experiment_metadata(xids[0])
    assert md['name']=='x1', 'Retrieved the wrong experiment'
  
    xids = pg.find_experiments(q2)
    assert len(xids)==0, 'Found a nonexistent experiment'
    
    xids = pg.find_experiments({})
    assert len(xids)==2, 'Couldnt find all the experiments'

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_bundles():
  with ProjectDB() as pg:
    x = pg.create_experiment_id('x')
    b = {'metadata': {'bundle_type':'placeholder', 'time':'now', 'id':'-1'}, 'data': {'values':[0, 1, 2]}}

    bid = pg.write_bundle(b, x)
    b2 = pg.find_bundles({}, x)[0]
    assert b['data']==b2['data'], 'data corrupted'
    assert len(b['metadata'])==len(b2['metadata']), 'incomplete metadata'
    assert b['metadata']['bundle_type']==b2['metadata']['bundle_type'], 'bundle type corrupted'
    assert b['metadata']['time']==b2['metadata']['time'], 'time corrupted'
    
