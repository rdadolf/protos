from utils import *
import os

STORAGE_SERVER=os.getenv('PROTOS_STORAGE_SERVER', '127.0.0.1')

# This creates a persistent default project table. It is NOT a regression test.
# Still, run it with 'nosetests <this-filename>' to get the right imports, etc.
@set_config(storage='postgres', storage_server=STORAGE_SERVER, project_name='default')
def populate_test_db():
  pg = protos.storage_adapters.postgres.Postgres()
  pg._set_role_rw()
  with protos.storage_adapters.postgres.Transaction(pg._conn) as x:
    x.execute('DROP TABLE "default_bundles"')
    x.execute('DROP TABLE "default"')
  pg = protos.storage_adapters.postgres.Postgres()

  ids = range(1,5)
  xids = []
  for i in ids:
    xid = pg.create_experiment_id('exp_'+str(i))
    xids.append(xid)
    md = {'id': xid,
          'name': 'exp_'+str(i),
          'host': 'localhost',
          'platform': '*nix',
          'user': 'me',
          'time': protos.internal.timestamp(),
          'progress': '60' }
    pg.write_experiment_metadata(md,xid)
    b = {'metadata': {'bundle_type':'placeholder', 'time':protos.internal.timestamp(), 'id':'-1'}, 'data': {'values':range(i,i+4)}}
    pg.write_bundle(b,xid)
    b2 = b
    b2['data']['values'] = range(i,i+5)
    b2['metadata']['time'] = protos.internal.timestamp()
    pg.write_bundle(b2,xid)
