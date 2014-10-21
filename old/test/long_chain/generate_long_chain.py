#!/usr/bin/env python

import os
import stat
import itertools
import random

random.seed(1)

a_z = list('abcdefghijklmnopqrstuvwxyz')

labels = list(itertools.combinations(a_z,2))
past_labels = []
for lab in labels:
  s = ''.join(lab)
  fname = s+'.protocol'
  f = open(fname, 'w')
  f.write('#!/usr/bin/env python')
  f.write('# '+s+'.protocol\n')
  f.write('import protos\n')
  if len(past_labels)>0:
    f.write("protos.require('"+random.choice(past_labels)+"')\n")
    f.write("protos.require('"+random.choice(past_labels)+"')\n")
    f.write("protos.require('"+random.choice(past_labels)+"')\n")
  f.close()
  os.chmod(fname,stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)
  
  past_labels.append(s)
