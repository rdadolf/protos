# Workflow
#
# Class definition for a workflow.
# Users will never explicitly define a workflow, but the dependence structure of their protocols implicitly does.
# Internally, however, we need to cache this information.
# If we didn't, we would have to re-build the dependence chains and re-read files from disk (really: NFS) everytime that we wanted to do global operations.

import analyze
import config

class Workflow:
  def __init__(self,protocol_file=None):
    if protocol_file is not None:
      self._deps = self.build_dependence_list_from_protocol(protocol_file)
    else:
      self._deps = dict()

  def build_dependence_list_from_protocol(self,protocol_file):
    calls = analyze.call_list_from_file(protocol_file)
    cfg_file = analyze.find_config_file(calls)
    prereqs = analyze.find_required_protocols(calls)
    print cfg_file
    cfg = config.Config(cfg_file)
    #print '[project] repo :',cfg.get('project','repo')
    #print '[project] protocol-dir :',cfg.get('project','protocol-dir')
    #print '[log] repo :',cfg.get('log','repo')

  def __repr__(self):
    return str(self._deps)
