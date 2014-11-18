import logging
import os.path
import tempfile
import shutil

from .config import config

# Expected project layout
# 
# project/
#   data/
#   experiments/
#   protocols/

def infer_from_exf(exf_path,config):
  '''
  Given a full path to an experiment file in a protos project, we should be able
  to reconstruct the rest of the directories and add them to a configuration.
  '''

  # Make sure the exf_path is real
  exf = os.path.realpath(exf_path)
  if not os.path.isfile(exf):
    logging.error('Experiment file '+str(exf)+' could not be found')
    return False

  # Infer and assign paths
  experiments_dir = os.path.dirname(exf)
  project_dir = os.path.dirname(experiments_dir)
  protocol_dir = os.path.join(os.path.dirname(experiments_dir),'protocols')
  data_dir = os.path.join(os.path.dirname(experiments_dir),'data')

  # Pass to experiment configuration
  config.experiments_dir = experiments_dir
  config.project_dir = project_dir
  config.protocol_dir = protocol_dir
  config.data_dir = data_dir

  return True


# Python context for temporary directory
class scratch_directory:
  def __init__(self):
    self.dir = None
  def __enter__(self):
    self.dir = tempfile.mkdtemp(prefix='/tmp/protos_temp_')
    logging.debug('Creating scratch directory '+self.dir)
    return self.dir
  def __exit__(self, type, value, traceback):
    if not config.preserve:
      logging.debug('Cleaning up scratch directory '+self.dir)
      # recursively delete whatever is in the scratch space
      assert os.path.isdir(self.dir), 'Scratch directory not found--something is wrong'
      assert len(self.dir)>1, 'Bad scratch directory name: "'+str(self.dir)+'"'
      shutil.rmtree(self.dir)
    return False # Don't suppress errors


