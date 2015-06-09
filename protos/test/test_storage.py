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
