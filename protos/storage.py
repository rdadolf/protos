import logging

mechanisms = {}

try:
  from .storage_adapters.fake import Fake
  mechanisms['fake'] = Fake
except Exception as e:
  logging.warn('Failed to import storage adapter Fake: '+str(e)+'. Disabling adapter.')

try:
  from .storage_adapters.mongo import Mongo
  mechanisms['mongo'] = Mongo
except Exception as e:
  logging.warn('Failed to import storage adapter Mongo: '+str(e)+'. Disabling adapter.')

try:
  from .storage_adapters.disk import Disk
  mechanisms['disk'] = Disk
except Exception as e:
  logging.warn('Failed to import storage adapter Disk: '+str(e)+'. Disabling adapter.')

try:
  from .storage_adapters.postgres import Postgres
  mechanisms['postgres'] = Postgres
except Exception as e:
  logging.warn('Failed to import storage adapter Postgres: '+str(e)+'. Disabling adapter.')
