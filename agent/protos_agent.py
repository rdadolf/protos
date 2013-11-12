#!/usr/bin/env python

import os
import sys
import protos



if __name__=='__main__':
  if len(sys.argv)<2:
    print 'Usage: '+os.path.basename(sys.argv[0])+' <protocol-file>'
    sys.exit(-1)
  final_protocol_file = sys.argv[1]

  # Build workflow
  workflow = protos.core.workflow.Workflow(final_protocol_file)

