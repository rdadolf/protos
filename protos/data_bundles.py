
import tempfile

# These tokens are used at experiment parse time to thread data dependencies
# without having to invoke protocol functions (which are monadic and never
# actually executed until run time).
class Bundle_Token:
  def __init__(self,v=-1):
    self.v=v
  @property
  def id(self):
    return self.v
  def __repr__(self):
    return 'Bundle_Token('+str(self.id)+')'

class Token_Generator:
  bundle_id = 0

  @classmethod
  def new(self):
    rv = self.bundle_id
    self.bundle_id += 1
    return Bundle_Token(rv)

# This is the actual reference to the data that a protocol generates.
class Data_Bundle:
  def __init__(self,tag_prefix='bundle'):
    data_directory = protos.data
    self.dir = tempfile.mkdtemp(prefix=tag_prefix)
    self.tag = 'bundle'
    pass
  def __str__(self):
    return self.tag

  # User-accessible functions
  def directory(self):
    return self.tag
