import logging

from .data_bundles import Data_Bundle, Bundle_Token

class Experiment:
  def __init__(self):
    self.schedule = []
    self.bundles = {}
    pass

  def _add(self, func, data_tok, args, kwargs):
    logging.debug('Adding function '+str(func))
    self.schedule.append( (func,data_tok,args,kwargs) )
    self.bundles[data_tok] = None
    pass

  def _run(self):
    logging.debug('Running experiment')
    for (f,tok,a,kw) in self.schedule:
      # Replace data bundle tokens with actual data bundles
      for (k,v) in kw.items():
        if isinstance(v,Bundle_Token):
          # FIXME: inverted data dependencies can cause this lookup to fail
          kw[k] = self.bundles[v.id]
      # Now run the function and store the resulting bundle object
      bundle = f(*a,**kw)
      # FIXME: assert isinstance(bundle,Data_Bundle), when bundles are ready
      self.bundles[tok.id] = bundle
    pass


# Experiment decorator
class experiment:
  def __init__(self,func):
    logging.debug('Found experiment "'+str(func.__name__)+'"')
    self.func = func

  # the 'experiment' arg is presented to the user as something that looks like a 
  # protocol module. It's not. It's an Experiment instance which we use to chain
  # together all of the protocol statements.
  def __call__(self, experiment, *args, **kwargs):
    logging.debug('Executing decorated experiment function')
    self.func(experiment, *args, **kwargs)
    return experiment
