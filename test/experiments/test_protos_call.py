import protos
import logging

@protos.experiment
def test_protos_call(protocols):
  # Make sure I/O buffers in protos.call don't overflow and deadlock the child process.
  dummy0 = protocols.test_protos_call.emit_large_stdout()
  
