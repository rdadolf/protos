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
import config

class Agent():
  def __init__(self, root_protocol_file):
    self.run(root_protocol_file) # Does not return

  def run(self, root_protocol_file):
    # First, find a configuration file
    self._options = config.Config()
    assert self._options.find_config_file(), "Couldn't find a valid config file. Try -c <file> or setting PROTOS_CONFIG."
      
    self._flow = workflow.Workflow(root_protocol_file, self._options)
    assert self._flow is not None, "Failed to compile workflow. Maybe a malformed protocol file?"

    self._workq = self._flow.toposort()
    assert self._workq is not None, "Couldn't compute workflow dependencies. Maybe check for circular dependencies?"

    for work_item in self._workq:
      print 'EXEC: ',work_item

    # All execution is complete. Do not return control to the user. Exit.
    sys.exit(0)
