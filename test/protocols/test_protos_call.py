import protos
from functools import reduce
import os.path
import logging

class Script_Output(protos.Bundle):
  def __init__(self, experiment):
    super().__init__(experiment, name='script_output')
    self.lines = 0

@protos.protocol
def emit_large_stdout(experiment, *_):

  script_path = reduce(os.path.join, [protos.home(), 'scripts', 'emit_large_stdout'])
  (out,err) = protos.call(script_path)
  logging.debug('Script complete.')

  ret = Script_Output(experiment)
  ret.lines = out.count('\n')
  assert ret.lines==100000, 'Line count is incorrect.'

  return ret
