import logging
import os.path

################################################################################
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
