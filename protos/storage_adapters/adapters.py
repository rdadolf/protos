
def _json_subset(pat,data,indent=0):
  '''Returns data if pat is a subset of the fields in data, None otherwise.'''

  if (type(data) is list) and (type(pat) is list):
    #print ' '*indent,'LIST:'#,pat,data
    for subpat in pat:
      if not any([_json_subset(subpat,subdata,indent+2) for subdata in data]):
        #print ' '*indent,'FAILED LIST'
        return None

  elif (type(data) is dict) and (type(pat) is dict):
    #print ' '*indent,'DICT:',pat.keys(),data.keys()
    if not all([pat_k in data.keys() for (pat_k,pat_v) in pat.items()]):
      #print ' '*indent,'FAILED DICT (KEY)'
      return None
    arry=[_json_subset(pat_v,data[pat_k],indent+2) for (pat_k,pat_v) in pat.items()]
    #if not all([_json_subset(pat_v,data[pat_k],indent+2) for (pat_k,pat_v) in pat.items()]):
    if not all(arry):
      #print ' '*indent,'FAILED DICT (VALUE)'
      return None

  else: # scalar
    #print ' '*indent,'SCALAR:',pat,data
    if pat!=data:
      #print ' '*indent,'FAILED SCALAR'
      return None

  #print ' '*indent,'PASSED'
  return data

class Datastore: # Abstract interface class
  def __init__(self):
    ''' Any storage initialization that needs to take place should happen here. Note that this function is called *at least* every time a bundle is initialized, so make sure that it *checks* expensive operations before blindly executing them.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def create_experiment_id(self, experiment_name):
    ''' This function should take experiment info and create a space for it on the datastore. It should return a unique identifier which can be reused for write_bundle. Calling it twice will create two different experiment ids.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def find_experiments(self, pattern):
    '''Returns a list of xid's for experiments that match the pattern given.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def read_experiment_metadata(self, xid):
    '''Returns a JSON dictionary of metadata.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def write_experiment_metadata(self, metadata, xid):
    ''' This should take a JSON dictionary of metadata and write it to the datastore, associated with the experiment as a whole. Bundles have their own metadata which is handled separately.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def find_bundles(self, pattern, xid):
    ''' Returns a list of data bundle objects.'''
    raise NotImplementedError('Missing implementation in storage adapter')

  def write_bundle(self, bundle, xid):
    ''' This function should take a serialized bundle and write it to whatever backing store it uses.'''
    raise NotImplementedError('Missing implementation in storage adapter')

