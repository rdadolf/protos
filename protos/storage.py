from .storage_adapters.fake import Fake
from .storage_adapters.mongo import Mongo
from .storage_adapters.mysql_adapter import MySQL
from .storage_adapters.disk import Disk

mechanisms = {
  'fake' : Fake,
  'mongo' : Mongo,
  'mysql' : MySQL,
  'disk' : Disk
}
