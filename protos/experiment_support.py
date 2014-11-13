import logging
import os
import os.path
from functools import reduce

from .data_bundles import Data_Bundle, Bundle_Token
from .config import config
from .fs_layout import scratch_directory

# Experiment Data:
#   'path' => path to the experiment data directory
#   'bundle_tag' => current bundle token id, a unique, monotonically increasing integer

class Experiment:
  # Be careful, this class is exposed to the user. Don't let stray data escape.
  def __init__(self,exp_deco):
    self._schedule = []
    self._bundles = {}
    self._path = reduce(os.path.join, [config.data_dir, exp_deco.name])
    self._name = exp_deco.name
    if not os.path.isdir(self._path):
      os.mkdir(self._path)
    logging.debug('Experiment directory is: '+str(self._path))

    pass

  def _add(self, func, data_tok, args, kwargs):
    logging.debug('Adding function '+str(func.__name__))
    self._schedule.append( (func,data_tok,args,kwargs) )
    self._bundles[data_tok] = None
    pass


  def _run(self):
    #logging.debug('Running experiment')
    print('--- Running Experiment "'+str(self._name)+'" ---')

    # FIXME: incremental progress is not handled
    #        we'll need to use _read_from_disk() to grab previous results
    #        we'll use those bundles to pre-populate the self._bundles
    #        then we'll need to skip forward to the starting spot and run

    for (f,tok,a,kw) in self._schedule:
      # Replace data bundle tokens with actual data bundles
      for (k,v) in kw.items():
        if isinstance(v,Bundle_Token):
          # FIXME: inverted data dependencies can cause this lookup to fail
          kw[k] = self._bundles[v.id]

      # Now run the function and store the resulting bundle object
      exp_data = { 'path': self._path, 'bundle_tag': tok.id }
      with scratch_directory() as d:
        os.chdir(d)
        # FIXME: Capture timing information?
        print('  Running protocol '+str(f.__name__))
        bundle = f(exp_data,*a,**kw)
        assert isinstance(bundle,Data_Bundle), 'Protocol "'+str(f.__name__)+'" returned a '+str(type(bundle))+' instead of a bundle object'

      # Now persist the bundle, for the record and for incremental re-eval later
      bundle._write_to_disk()

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
