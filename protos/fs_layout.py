import logging
import os.path
import tempfile
import shutil

from .config import config

# Expected project layout
# 
# root/
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
  config.experiments_dir = os.path.dirname(exf)
  root_dir = os.path.dirname(config.experiments_dir)
  config.protocol_dir = os.path.join(root_dir,'protocols')
  config.data_dir = os.path.join(root_dir,'data')

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


