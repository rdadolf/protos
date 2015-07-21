# Add ourselves to PYTHONPATH
import sys
sys.path.append('/var/www/protos')

# Flask needs the "as applicaiton" part.
from dashboard import app as application
