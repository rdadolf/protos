# Workflow
#
# Class definition for a workflow.
# Users will never explicitly define a workflow, but the dependence structure of their protocols implicitly does.
# Internally, however, we need to cache this information.
# If we didn't, we would have to re-build the dependence chains and re-read files from disk (really: NFS) everytime that we wanted to do global operations.

import analyze
import config
import warnings
import os

class Workflow:
  def __init__(self,protocol_file=None):
    if protocol_file is not None:
      (self._deps, self._filename_cache) = self.build_dependencies(protocol_file)
    else:
      self._deps = dict() # protocol -> [protocols, ...]
      self._filename_cache = dict() # protocol -> filename
    print 'DEPS'
    for (k,v) in self._deps.items():
      print k,'->',v
    print 'FILES'
    for (k,v) in self._filename_cache.items():
      print k,'->',v

  def build_dependencies(self,given_protocol_file):
    # General idea: BFS on the dependence tree.
    dependencies = dict() # protocol-name => (protocol-file, [dep-name, ...]
    filename_cache = dict() # protocol -> filename
    work_q = [] # [ (name,file), ...]

    # First, guess at our protocol name. They're not embedded in the files, but
    # if we parse the starting file, we can probably get it right. This is not
    # usually important, except for detecting errors (cycles) which include the
    # final protocol.
    protocol_file = os.path.abspath(given_protocol_file)
    (prefixpath,name) = os.path.split(protocol_file)
    if name.endswith('.protocol'):
      protocol_name = name[0:name.rfind('.protocol')]
    else:
      protocol_name = name

    work_q = [ (protocol_name, protocol_file) ]
    filename_cache = { protocol_name : protocol_file }
    dependencies = { protocol_name : (protocol_file, []) }

    ## Compute the first horizon directly
    #analysis = analyze.Analysis(protocol_file)
    #if analysis is None:
    #  warnings.warn('Failed to analyze protocol file "'+work+'".')
    #cfg_file = analysis.find_config_file()
    #cfg = config.Config(cfg_file)
    #ppath = cfg.get('project','protocol-path')
    #predicted_file = config.expand_protocol_path(protocol_name,ppath)
    ## Check if our guess was right. We can't do anything except warn, though.
    #if protocol_file!=predicted_file:
    #  warnings.warn('Protocol file given ("'+str(given_protocol_file)+'") didn\'t match what we found ("'+str(predicted_file)+'")')
    #if protocol_name not in filename_cache:
    #  filename_cache[protocol_name] = protocol_file
    ## We've already done most of the work, may as well do the first horizon
    #deps = list(set(analysis.find_required_protocols())) # unique dependencies
    #dependencies[protocol_name] = (protocol_file, deps)
    #print 'DEPS:',deps
    #print 'PPATH:',ppath
    #for dep in deps:
    #  if dep not in filename_cache:
    #    filename_cache[dep] = config.expand_protocol_path(dep,ppath)
    #  deppath = filename_cache[dep]
    #  if deppath is None:
    #    warnings.warn('Missing protocol file: '+str(deppath))
    #  print 'DEPPATH:',deppath
    #  work_q.append( (dep,deppath) )

    while len(work_q)>0:
      print 'WORK_Q',work_q
      # Grab the top of the work queue
      (work,workfile) = work_q.pop()
      if work not in dependencies: # This should always be the case
        dependencies[work] = (workfile, [])
      # Find and load config file
      analysis = analyze.Analysis(workfile)
      if analysis is None:
        warnings.warn('Analysis of protocol file "'+work+'" failed.')
      cfg_file = analysis.find_config_file()
      cfg = config.Config(cfg_file)
      # Grab protocols path
      ppath = cfg.get('project','protocol-path')
      # Process all protocols
      protos = analysis.find_required_protocols()
      all_observed = [dep for deps in dependencies.values() for dep in deps]
      for proto in protos:
        # Expand filenames
        if proto not in filename_cache:
          filename_cache[proto] = config.expand_protocol_path(proto,ppath)
        proto_filename = filename_cache[proto]
        # Add them to the dependence tree, if necessary
        if proto_filename not in dependencies[work][1]:
          dependencies[work][1].append(proto_filename)
        # Check if they've *ever* been looked by any node
        if proto not in all_observed:
          # It's new, expand their names and add it
          work_q.append( (proto, proto_filename) )

    return dict([(k,v[1]) for (k,v) in dependencies.items()]), filename_cache

  def __repr__(self):
    return str(self._deps)
