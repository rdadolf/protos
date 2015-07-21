from utils import *

##### Make sure adapters return sane values for null requests.

@set_config(data_dir='/tmp/data', storage='fake')
def test_fake_expsearch():
  xs = protos.query.search_experiments({})
  assert type(xs) is list, 'Bad return value'

@set_config(data_dir='/tmp/data', storage='disk')
def test_disk_expsearch():
  xs = protos.query.search_experiments({})
  assert type(xs) is list, 'Bad return value'

#FIXME: find test server to use
#@set_config(data_dir='/tmp/data', storage='mongo', storage_server='')
#def test_mongo_expsearch():
#  xs = protos.query.search_experiments({})
#  assert type(xs) is list, 'Bad return value'

# FIXME: don't use the production server
STORAGE_SERVER='brinsop.int.seas.harvard.edu'

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
def test_pg_authentication():
  pg = protos.storage_adapters.postgres.Postgres()
  assert pg._conn.closed==0, 'Connection failed'

@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='test_project')
def test_project_table_creation():
  pg = protos.storage_adapters.postgres.Postgres()
  pg._init_project_idempotently('test')
  # should be a table named 'test' now
  
  with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
    x.execute('SELECT xid FROM test WHERE false')
  pass
