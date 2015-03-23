import logging
import os
import os.path
from functools import reduce

from .data_bundles import Experiment_Data, Data_Bundle, Bundle_Token
from .config import config
from .fs_layout import scratch_directory
from .internal import timestamp

from .storage import mechanisms as storage_mechanisms

# Namespace is a placeholder class for allowing hierarchy in protocol names.
# This is a little tricky. We add protocol names to the Experiment instance
# at runtime, but since protocols are fake-invoked using the same dot syntax
# normal class attribute lookups, we have to also populate the dictionaries.
# For example, an experiment contains this:
#
# @protos.experiment
# def example(protocols):
#   var = protocols.directory.filename.protocol_function(args)
#
# When we actually run the example function (which is an experiment), we're
# actually just populating the _schedule of an Experiment instance with a list
# of what protocols *will be* called. So "protocol_function" should be scheduled
# when the experiment is actually run. To do this, when protos loads all the
# protocol functions in the first place, it replaces them with thunks that add
# themselves to the experiment instance. Unfortunately, what it's replacing is
# the whole name '.directory.filename.protocol_function' attribute of the 
# experiment, which isn't just one entity. It's actually a chain of attribute
# lookups, first finding 'directory' in the experiment, then 'filename' in 
# whatever thing is returned from that lookup, etc. *This stub class is that
# thing.*  Basically, it allows a chain of attribute lookups in an experiment. 
# So the example above will turn into:
# (at experiment-construction time:)
#   getattr( protocols, 'directory' ) => Namespace n0
#   getattr( n0, 'filename' ) => Namespace n1
#   getattr( n1, 'protocol_function' ) => anonymous protocol thunk
#   <call anonymous protocol thunk> => adds protocol function and returns a token
# The protos protocol loader would have constructed the chain of n0,n1,etc.
class Namespace:
  def __init__(self, nsroot):
    self._nsroot = nsroot

class Experiment:
  # Be careful, this class is exposed to the user. Don't let stray data escape.
  def __init__(self,exp_deco):
    self._schedule = []
    self._bundles = {}
    self._path = reduce(os.path.join, [config.data_dir, exp_deco.name])
    self._name = exp_deco.name
    self._metadata = {
      'name': self._name,
    }
    self._nsroot = self # for namespace resolution

    # Initialize our storage interface
    assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
    self._storage = storage_mechanisms[config.storage]()
    self._storage_xid = self._storage.create_experiment_id(self._name)
    self._storage.update_experiment_metadata(self._metadata, self._storage_xid)

  def _add(self, func, data_tok, args, kwargs):
    logging.debug('Adding function '+str(func.__name__))
    # list(args) is needed later when we substitute bundles for bundle tokens
    self._schedule.append( (func,data_tok,list(args),kwargs) )
    self._bundles[data_tok] = None
    pass

  def _run(self):
    #logging.debug('Running experiment')
    print('--- Running Experiment "'+str(self._name)+'" ---')
    self._metadata['time'] = timestamp()
    self._storage.update_experiment_metadata(self._metadata, self._storage_xid)

    # FIXME: incremental progress is not handled
    #        we'll need to use _read_from_disk() to grab previous results
    #        we'll use those bundles to pre-populate the self._bundles
    #        then we'll need to skip forward to the starting spot and run

    for (f,tok,a,kw) in self._schedule:
      # Replace data bundle tokens with actual data bundles
      # First for keyword arguments
      for (k,v) in kw.items():
        if isinstance(v,Bundle_Token):
          # FIXME: inverted data dependencies can cause this lookup to fail
          kw[k] = self._bundles[v.id]
      # And for positional arguments
      for i in xrange(0,len(a)):
        arg = a[i]
        if isinstance(arg,Bundle_Token):
          # FIXME: above may still apply (I don't remember!)
          a[i] = self._bundles[arg.id]

      # Now run the function and store the resulting bundle object
      xdata = Experiment_Data(tok.id, self._storage, self._storage_xid)
      with scratch_directory() as d:
        os.chdir(d)
        # FIXME: Capture timing information?
        print('  Running protocol '+str(f.__name__))
        bundle = f(xdata,*a,**kw)
        assert isinstance(bundle,Data_Bundle), 'Protocol "'+str(f.__name__)+'" returned a '+str(type(bundle))+' instead of a bundle object'

      # Now persist the bundle, for the record and for incremental re-eval later
      bundle._persist()

      self._bundles[tok.id] = bundle

    print('Done.')
    return True


# Experiment decorator
class experiment:
  def __init__(self,wrapped_func):
    self.name = str(wrapped_func.__name__)
    logging.debug('Found experiment "'+self.name+'"')
    self.func = wrapped_func

  # the 'experiment' arg is presented to the user as something that looks like a
  # protocol module. It's not. It's an Experiment instance which we use to chain
  # together all of the protocol statements.
  def __call__(self, experiment, *args, **kwargs):
    logging.debug('Building experiment')
    self.func(experiment, *args, **kwargs)
    return experiment
