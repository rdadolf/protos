import logging

class Experiment:
  def __init__(self):
    self.schedule = []
    pass

  def _add(self, func, args, kwargs):
    logging.debug('Adding function '+str(func))
    self.schedule.append( (func,args,kwargs) )
    pass

  def _run(self):
    logging.debug('Running experiment')
    for (f,a,kw) in self.schedule:
      f(*a,**kw)
    pass
  

# Experiment decorator
class experiment:
  def __init__(self,func):
    logging.debug('Found experiment "'+str(func.__name__)+'"')
    logging.debug('deco globals: '+str(globals().keys()))
    logging.debug('deco locals: '+str(locals().keys()))
    self.func = func

  # the 'experiment' arg is presented to the user as something that looks like a 
  # protocol module. It's not. It's an Experiment instance which we use to chain
  # together all of the protocol statements.
  def __call__(self, experiment, *args, **kwargs):
    logging.debug('Executing decorated experiment function')
    logging.debug('func globals: '+str(globals().keys()))
    logging.debug('func locals: '+str(locals().keys()))

    self.func(experiment, *args, **kwargs)

    return experiment
