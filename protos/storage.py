from .storage_adapters.fake import Fake
from .storage_adapters.mongo import Mongo
from .storage_adapters.disk import Disk
from .storage_adapters.postgres import Postgres

mechanisms = {
  'fake' : Fake,
  'mongo' : Mongo,
  'postgres' : Postgres,
  'disk' : Disk
}
