# Workflow
#
# Class definition for a workflow.
# Users will never explicitly define a workflow, but the dependence structure of their protocols implicitly does.
# Internally, however, we need to cache this information.
# If we didn't, we would have to re-build the dependence chains and re-read files from disk (really: NFS) everytime that we wanted to do global operations.

import analyze
import config
import warnings
import os

class Workflow:
  def __init__(self, protocol_file, configuration):
    self._deps = self.build_dependencies(protocol_file, configuration)

  def build_dependencies(self, given_protocol_file, configuration):
    # General idea: BFS on the dependence tree.
    dependencies = dict() # protocol-name => [protocol-name, ...]
    past_work = set() # things flushed from the work queue (don't analyze twice)
    work_q = [] # [ name, ...]

    # Grab the first protocol name
    protocol_file = os.path.abspath(given_protocol_file)
    protocol_name = analyze.protocol_name_from_file(protocol_file)

    work_q = [ protocol_name ]
    dependencies = { protocol_name : set([]) }

    while len(work_q)>0:
      # Grab the top of the work queue, mark it looked-at
      work = work_q.pop()
      workfile = configuration.expand_protocol_path(work)
      if work not in dependencies:
        # This should always be the case, but it's not fatal if it's not
        dependencies[work] = (workfile, set([]))
      past_work.add(work)

      # Process all protocols
      analysis = analyze.Analysis(workfile)
      for dep in analysis.find_required_protocols():
        dependencies[work].add(dep)

    return dependencies

  def toposort(self):
    warnings.warn('FIXME: replace with actual implementation') # FIXME
    return self._deps.keys() # NOT topo-sorted

  def __repr__(self):
    return str(self._deps)
