import logging
import sys
import os
import os.path
from functools import reduce
import socket
import pwd
import platform

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

# Built-ins are special pseudo-protocols that are provided by protos itself.
# These functions are called when the experiment is built, not run.
# These may or may not return bundles.
class Builtins(Namespace):
  def __init__(self, exp, nsroot):
    Namespace.__init__(self, nsroot)
    self.exp = exp

  def tag(self, t):
    self.exp._metadata['tags'].append(str(t))
    return None

class Experiment:
  # Be careful, this class is exposed to the user. Don't let stray data escape.
  def __init__(self,exp_deco):
    self._schedule = []
    self._bundles = {}
    self._path = reduce(os.path.join, [config.data_dir, exp_deco.name])
    self._name = exp_deco.name
    self._metadata = {
      'name': self._name,
      'tags': [],
    }
    self._nsroot = self # for namespace resolution
    self.builtin = Builtins(self, self._nsroot) # instantiate our builtin protocols

    # Initialize our storage interface
    assert config.storage in storage_mechanisms, 'Could not find a data storage adapter name "'+config.storage+'"'
    self._storage = storage_mechanisms[config.storage]()
    self._storage_xid = self._storage.create_experiment_id(self._name)
    self._metadata['id'] = str(self._storage_xid)
    self._storage.write_experiment_metadata(self._metadata, self._storage_xid)

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
    hostname = socket.getfqdn()
    dot_loc = hostname.find('.')
    if dot_loc>0:
      hostname = hostname[0:dot_loc]
    self._metadata['host'] = hostname
    self._metadata['platform'] = platform.platform()
    self._metadata['user'] = pwd.getpwuid(os.getuid())[0]
    self._storage.write_experiment_metadata(self._metadata, self._storage_xid)

    self._metadata['progress'] = 0
    self._metadata['last_error'] = ''

    with scratch_directory() as xscratch:
      self._xscratch = xscratch
      progress_count = 0
      progress_total = len(self._schedule)
      for (f,tok,a,kw) in self._schedule:
        # Replace data bundle tokens with actual data bundles
        # First for keyword arguments
        for (k,v) in kw.items():
          if isinstance(v,Bundle_Token):
            # FIXME: buggy inverted data dependencies can cause this lookup to fail
            kw[k] = self._bundles[v.id]
        # And for positional arguments
        for i in xrange(0,len(a)):
          arg = a[i]
          if isinstance(arg,Bundle_Token):
            # FIXME: buggy inverted data dependencies can cause this lookup to fail
            a[i] = self._bundles[arg.id]

        # Now run the function and store the resulting bundle object
        xdata = Experiment_Data(tok.id, self._storage, self._storage_xid, self._xscratch)
        with scratch_directory() as d:
          os.chdir(d)
          # FIXME: Capture timing information?
          print('  Running protocol '+str(f.__name__))
          try:
            bundle = f(xdata,*a,**kw)
            assert isinstance(bundle,Data_Bundle), 'Protocol "'+str(f.__name__)+'" returned a '+str(type(bundle))+' instead of a bundle object'
          except:
            e = sys.exc_info()[1]
            logging.error('Protocol "'+str(f.__name__)+'" failed.')
            self._metadata['last_error'] = str(e)
            self._storage.write_experiment_metadata(self._metadata, self._storage_xid)
            raise

        # Now persist the bundle, for the record and for incremental re-eval later
        bundle._persist()

        # Update our progress
        progress_count += 1
        self._metadata['progress'] = str(100*progress_count/progress_total)
        self._storage.write_experiment_metadata(self._metadata, self._storage_xid)

        self._bundles[tok.id] = bundle

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
