
class Configuration:
  def __init__(self):
    self.params = dict()
  # Can act like a dict for arbitrary parameters
  def __len__(self):
    return len(self.params)
  def __getitem__(self,k):
    return self.params[k]
  def __setitem__(self,k,v):
    self.params[k]=v

