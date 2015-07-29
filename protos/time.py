import logging
import os
import os.path
from datetime import datetime

# Common timestamp format.
# We use timestamps all over protos, and it's too easy to use different
# standards and formats. Time is:
#   a human-readable string
#   UTC
#   microsecond-resolution
#   relative to year 0 AD
#   24-hour
def timestamp():
  return datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f_UTC')

# If a computer needs to understand a timestamp, turn it into a datetime object.
# Note that timezone is not explicit in this object. Assume UTC.
def parse_timestamp(stamp):
  return datetime.strptime(stamp,'%Y-%m-%d_%H-%M-%S-%f_UTC')
