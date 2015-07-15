import os
import os.path
from functools import reduce
import pwd
import logging
import mysql
import mysql.connector

from ..config import config
from ..internal import timestamp
from .adapters import Datastore, _json_subset

class MySQL(Datastore):
  def __init__(self):
    pass

  def create_experiment_id(self, experiment_name):
    return '1'

  def find_experiments(self, pattern):
    return ['1']

  def read_experiment_metadata(self, xid):
    return {}

  def write_experiment_metadata(self, metadata, xid):
    return True

  def find_bundles(self, pattern, xid):
    return []
 
  def write_bundle(self, bundle, xid):
    return True
