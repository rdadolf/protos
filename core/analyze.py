# Analyze
# 
# Parse and analyze protocol files for static-time information.

import sys
import ast
import warnings
import config
import protos_api

PROTOS_NAME = 'protos'
PROTOS_FUNCTIONS = protos_api.FUNCTIONS
PROTOS_ALL = '*' # Magic value, value is arbitrary. It is NOT a list.

class Analysis:
  def __init__(self,filename):
    self._filename = filename
    self._prog = None
    self._mod_names = None
    self._calls = None
    self.parse(str(filename))

  def parse(self,filename):
    self._prog = ast.parse(open(filename).read())
    self._mod_names = self.find_module_names()
    self._calls = self.find_calls()

  def line_prefix_at_loc(src,line,col):
    ''' Helper function for error messages. '''
    return src.split('\n')[line-1][col:]

  def find_module_names(self):
    '''
    Finds all of the import statements in the program and returns the ones that
    refer to Protos. Return value is a dictionary of the imported name and either
    a list of definition names or PROTOS_ALL (to indicate everything).
    '''
    # Find the protocol import/importfrom expressions and fin
    mod_names = dict({'':[]}) # name -> [aliases] or PROTOS_ALL
    for child in ast.walk(self._prog):
      # import _,_,...
      if isinstance(child, ast.Import):
        for module_alias in child.names:
          if module_alias.name==PROTOS_NAME:
            if module_alias.asname is None:
              mod_names[PROTOS_NAME] = PROTOS_ALL
            else:
              mod_names[module_alias.asname] = PROTOS_ALL
  
      # from _ import _,_,...
      if isinstance(child, ast.ImportFrom):
        if str(child.module)==PROTOS_NAME:
          # Found one, add its aliases to the dictionary
          for alias in child.names:
            if str(alias.name)=='*':
              mod_names[''] = PROTOS_ALL
            elif mod_names[''] == PROTOS_ALL:
              break # If we already have everything, no need to add anything
            else:
              tup = (alias.name,alias.asname)
              if tup not in mod_names['']:
                mod_names[''].append( tup )
    return mod_names

  def find_calls(self):
    '''
    Finds all calls to the protos module and returns them.
    Transform imported names into their canonical forms.
    (i.e.- 'from protos import require as req' followed by 'req("something")' will
    still return 'require' in the output call list.
    Returns a list of (name,args,kws,stargs,kwargs); some arguments may be None.
    '''
    # Find all the things that cound
    if self._mod_names['']==PROTOS_ALL:
      top_funcs = PROTOS_FUNCTIONS
    else:
      top_funcs = [ n[1-(n[1] is None)] for n in self._mod_names[''] ]
    top_mods = [n for n in self._mod_names.keys() if n!='']
    #print top_funcs
    #print top_mods
  
    calls = []
    for child in ast.walk(self._prog):
      if isinstance(child, ast.Call):
        # Call: func, args, keywords, starargs, kwargs
        # However, in a module call, func is the module name.
  
        if isinstance(child.func, ast.Name): # Bare call
          ref = child.func.id
          if ref in top_funcs:
            # transform call names back into their canonical form
            name = None
            if ref in PROTOS_FUNCTIONS:
              name = ref
            else:
              for (n,asn) in self._mod_names['']:
                if ref==asn:
                  name = n
                  break
            if name is None:
              warnings.warn('Analyzer is confused. We thought there was a Protos call, but we can\'t figure out which one it was. Maybe PROTOS_FUNCTIONS is out of date?')
            # Now return the call
            calls.append( (name, child.args, child.keywords, child.starargs, child.kwargs) )
          
        elif isinstance(child.func, ast.Attribute):
          # Module call.
          # Protos has no levels, so only find single-level calls.
          if isinstance(child.func.value, ast.Name): # alternative is ast.Attribute
            mod = child.func.value.id
            name = child.func.attr
            if mod in top_mods:
              if self._mod_names[mod]==PROTOS_ALL:
                calls.append( (name, child.args, child.keywords, child.starargs, child.kwargs) )
              else:
                warnings.warn('I don\'t think there\'s a way to import just some parts of a module without also making it a bareword. If you\'re seeing this, that\'s not true. Please let me know so I can fix it.')
  
    return calls
    
  def find_config_file(self):
    '''
    Finds the 'config()' call in the list of calls.
    There should only be one, and the first is returned.
    '''
    for (n,args,kws,stargs,kwargs) in self._calls:
      if n=='config':
        if len(args)!=1:
          warnings.warn('"config()" called with more than one argument')
        filename = str(args[0].s)
        path = config.expand_config_path(filename)
        return path
    warnings.warn('No config file found.')
    return None

  def find_required_protocols(self):
    '''
    Finds all of the 'require()' calls in the list of calls.
    Returns the names of the protocols that they specify.
    '''
    required = []
    for (n,args,kws,stargs,kwargs) in self._calls:
      if n=='require':
        if len(args)!=1:
          warnings.warn('"require()" called with more than one argument')
        proto = str(args[0].s)
        required.append(proto)
    return required


if __name__=='__main__':
  print 80*'v'
  analysis = Analysis(sys.argv[1])
  print 80*'^'
  print analysis.find_config_file()
  print analysis.find_required_protocols()
