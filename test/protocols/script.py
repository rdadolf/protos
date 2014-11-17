import protos
from functools import reduce
import os.path
import logging

@protos.protocol
def run(experiment, *_, script=None):

  script_path = reduce(os.path.join, [protos.home(), 'scripts', script])
  (out,err) = protos.call(script_path)
  logging.debug('Script complete.')

  f_out = open('out','w')
  f_out.write(out)
  f_out.close()
  f_err = open('err','w')
  f_err.write(err)
  f_err.close()

  ret = protos.Bundle(experiment,'script')
  ret.add_file('out')
  ret.add_file('err')

  return ret
