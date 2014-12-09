#!/usr/bin/env python3
import subprocess as sub
import os
from functools import reduce
import signal

failed = 0
attempted = 0
for test in os.listdir('experiments'):
  cmd = 'protos -v '+os.path.join('experiments',test)
  proc = sub.Popen(cmd, shell=True, universal_newlines=True, stdout=sub.PIPE, stderr=sub.PIPE)
  attempted += 1
  try:
    (out,err) = proc.communicate(timeout=10) # 10 seconds
    # FIXME? this output is not recorded. For now, if something fails, just run
    #        it manually and investigate.
    with open(os.path.join('log',test+'.out'),'w') as f:
      f.write(out)
    with open(os.path.join('log',test+'.err'),'w') as f:
      f.write(err)
    ret = proc.returncode
  except sub.TimeoutExpired:
    proc.kill()
    ret = -1 * signal.SIGKILL
  s='{experiment:.<50}[{status}]'
  if ret!=0:
    print(s.format(experiment=test,status='FAIL'))
    failed += 1
  else:
    print(s.format(experiment=test,status='PASS'))

print(80*'_')
print('{passed}/{attempted} tests passed.'.format(passed=attempted-failed, attempted=attempted))
