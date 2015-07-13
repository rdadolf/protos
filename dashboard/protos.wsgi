# Add ourselves to PYTHONPATH
import sys
sys.path.append(0,'/var/www/protos')

# Flask needs the "as applicaiton" part.
from dashboard.dashboard import app as application
