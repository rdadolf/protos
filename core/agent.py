# Agent
#
# The work manager, invoked when the first protos library import is called.
# Instead of loading functions, the protos package __init__ function hijacks
# control of the program and invokes this agent instead. The agent then
# builds a complete workflow DAG from static analysis of the original file
# and all of its specified dependencies (through protos.require()). Using
# a topological sort of the DAG, the agent then executes all of the specied
# scripts in order.

import sys
import workflow

class Agent():
  def __init__(self, root_protocol_file):
    self._flow = workflow.Workflow(root_protocol_file)
    self._workq = self._flow.toposort()
    self.run() # Does not return

  def run(self):
    assert self._flow is not None
    assert self._workq is not None

    for work_item in self._workq:
      print 'EXEC: ',work_item

    # All execution is complete. Do not return control to the user. Exit.
    sys.exit(0)
