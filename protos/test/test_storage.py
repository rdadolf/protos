from utils import *
import os

##### Make sure adapters return sane values for null requests.

@set_config(data_dir='/tmp/data', storage='fake')
def test_fake_expsearch():
  xs = protos.query.search_experiments({})
  assert type(xs) is list, 'Bad return value'

@set_config(data_dir='/tmp/data', storage='disk')
def test_disk_expsearch():
  xs = protos.query.search_experiments({})
  assert type(xs) is list, 'Bad return value'

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

@set_config(storage='postgres', storage_server=STORAGE_SERVER)
def reset_project(connection):
  pg = protos.storage_adapters.postgres.Postgres()
  with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
    x.execute('DROP TABLE IF EXISTS test_project CASCADE')
  pass

@set_config(storage='postgres', storage_server=STORAGE_SERVER)
def test_pg_authentication():
  pg = protos.storage_adapters.postgres.Postgres()
  assert pg._conn.closed==0, 'Connection failed'

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_init():
  pg = protos.storage_adapters.postgres.Postgres()
  # should be a table named 'test_project' (from the config)
  
  with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
    x.execute('SELECT xid FROM test_project WHERE false')
    # We don't care about the result. Just testing whether the table exists.

  reset_project(pg)

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_xid():
  pg = protos.storage_adapters.postgres.Postgres()

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

  reset_project(pg)

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_experiment_metadata():
  pg = protos.storage_adapters.postgres.Postgres()

  xid = pg.create_experiment_id('x1')
  md = pg.read_experiment_metadata(xid)
  assert type(md)==type({}), 'Incorrect return type for experiment metadata'

  reset_project(pg)
