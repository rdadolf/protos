# Provided interface

# This somewhat-convoluted way of importing the API is because the function
# list is needed in other parts of the code, and we want to avoid circular
# references by importing the package-level __init__ in internal modules.
# Instead, we define it one place, separately, then jump through some hoops
# here to import and define all those functions.

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
