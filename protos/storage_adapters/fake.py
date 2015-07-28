import logging
import json

from ..config import config
from ..internal import timestamp
from .adapters import Datastore

class Fake(Datastore):
  def __init__(self):
    pass
  def create_experiment_id(self, experiment_name):
    logging.debug('NEW EXP ID: 5')
    return '5'
  def find_experiments(self,pattern):
    logging.debug('FIND EXPS: '+str(pattern))
    return []
  def read_experiment_metadata(self, xid):
    logging.debug('READ EXP-METADATA: '+str(xid))
    return {}
  def write_experiment_metadata(self, metadata, xid):
    logging.debug('WRITE EXP-METADATA: '+json.dumps(metadata))
  def find_bundles(self, pattern, xid):
    logging.debug('FIND BUNDLES: '+str(pattern))
    return []
  def write_bundle(self, bundle, xid):
    logging.debug('BUNDLE:')
    logging.debug('DATA: '+json.dumps(bundle['data']))
    logging.debug('METADATA: '+json.dumps(bundle['metadata']))
    logging.debug('FILES: '+json.dumps(bundle['files']))
  def delete_experiment(self, xid):
    logging.debug('DELETE EXP: '+str(xid))
