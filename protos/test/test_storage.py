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

