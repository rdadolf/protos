import protos
import protos.query
import nose

def set_config(**kwargs):
  def test_decorator(func):
    @nose.tools.make_decorator(func)
    def wrapper(*a,**kw):
      for (k,v) in kwargs.items():
        if hasattr(protos.config,k):
          setattr(protos.config,k,v)
      func(*a,**kw)
    return wrapper
  return test_decorator
