# Provided interface

# This somewhat-convoluted way of importing the API is because the function
# list is needed in other parts of the code, and we want to avoid circular
# references by importing the package-level __init__ in internal modules.
# Instead, we define it one place, separately, then jump through some hoops
# here to import and define all those functions.

import core.agent

# Pull the Protos API
from core.protos_api import FUNCTIONS

# Setup package information
__all__ = FUNCTIONS

# Load the functions
mod=__import__('core.protos', globals(), locals(), FUNCTIONS, level=-1)
# Expose them to the user
for f in FUNCTIONS:
  globals()[f] = getattr(mod,f)

# Now clean up our namespace
#del core

################################################################################
# Hijack control
#
# Unlike normal modules, protos doesn't provide functions. It assumes control of
# the program and executes a dependent chain of protocols. The original script
# is merely a convenient way of pointing protos to the last dependency in the
# series.

# This is a way to get the name of the original file caused us to be imported.
# Protos should not be executed from an interactive session (you will not get
# control returned to you).
from __main__ import __file__ as root_protocol_file

core.agent.Agent(root_protocol_file)

# Control does not return, nothing should be below this line.
################################################################################
