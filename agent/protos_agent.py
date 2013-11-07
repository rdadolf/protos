#!/usr/bin/env python

import sys
import protos



if __name__=='__main__':
  if len(sys.argv)<2:
    print 'Usage: '+str(sys.argv[0])+' <protocol-file>'
  final_protocol_file = sys.argv[1]

  # Build workflow
  workflow = protos.core.workflow.Workflow(final_protocol_file)

