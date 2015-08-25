mechanisms = {}

try:
  from .storage_adapters.fake import Fake
  mechanisms['fake'] = Fake
except e:
  logging.warn('Failed to import storage adapter "Fake": '+str(e))

try:
  from .storage_adapters.mongo import Mongo
  mechanisms['mongo'] = Mongo
except e:
  logging.warn('Failed to import storage adapter "Mongo": '+str(e))

try:
  from .storage_adapters.disk import Disk
  mechanisms['disk'] = Disk
except e:
  logging.warn('Failed to import storage adapter "Disk": '+str(e))

try:
  from .storage_adapters.postgres import Postgres
  mechanisms['postgres'] = Postgres
except e:
  logging.warn('Failed to import storage adapter "Postgres": '+str(e))
