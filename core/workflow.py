# Workflow
#
# Class definition for a workflow.
# Users will never explicitly define a workflow, but the dependence structure of their protocols implicitly does.
# Internally, however, we need to cache this information.
# If we didn't, we would have to re-build the dependence chains and re-read files from disk (really: NFS) everytime that we wanted to do global operations.

class Workflow:
  def __init__(self):
    pass
