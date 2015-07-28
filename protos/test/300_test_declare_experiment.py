from utils import *

@protos.experiment
def example_experiment(protocols):
  pass

@set_config(storage='fake')
def test_experiment_exists():
  x = protos.experiment_support.Experiment(example_experiment)
  for md_tag in ['name','tags']:
    assert md_tag in x._metadata, 'Corrupt experiment metadata'
  assert isinstance(x._storage, protos.storage_adapters.adapters.Datastore), 'Storage mechanisms never initialized'
  
  pass
