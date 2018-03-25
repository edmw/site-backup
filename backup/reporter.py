# coding: utf-8
"""
Mixin and Decorators to collect and report
success and failure of function calls. 

To use add the mixin to a class
and decorate the functions to be observed:

class IDoSomething(Reporter, object):

  @ReporterCheck
  def doSomething(self):
    ...

  @ReporterCheckResult
  def iWillReturnAResult(self):
    ...

Then call object.reportResults() any time to generate a report.
"""

import re

from functools import wraps

from backup.utils import formatkv

# regular expression to convert camel case to space separated words
re_camel = re.compile(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))")

class Reporter(object):
  """ Mixin to store and report success and failure of function calls.
  """
  def __init__(self):
    self.parameters = dict()
    self.results = dict()

  def storeParameter(self, fname, name, value):
    """ Store parameter and value for the given function.

        For consecutive calls with the same function name
        parameters will be stored in a list.
    """
    fname = re_camel.sub(r" \1", fname.strip('_')).upper()
    if fname in self.parameters:
        if type(self.parameters[fname]) is list:
            self.parameters[fname].append((name, value))
        else:
            self.parameters[fname] = [self.parameters[fname], (name, value)]
    else:
        self.parameters[fname] = (name, value)

  def storeResult(self, fname, result):
    """ Store result for the given function.

        For consecutive calls with the same function name
        results will be stored in a list.
    """
    fname = re_camel.sub(r" \1", fname.strip('_')).upper()
    if fname in self.results:
      if type(self.results[fname]) is list:
        self.results[fname].append(result)
      else:
        self.results[fname] = [self.results[fname], result]
    else:
      self.results[fname] = result

  def reportParameters(self):
    """ Report parameters as fomatted string of key and value pairs.
    """
    kv = []
    for fname, parameters in self.parameters.items():
        if type(parameters) is list:
            for name, value in parameters:
                kv.append(("{} ({})".format(fname, name), value))
        elif type(parameters) is tuple:
            name, value = parameters
            kv.append(("{} ({})".format(fname, name), value))
        else:
            kv.append(fname, parameters)
    return formatkv(kv)

  def reportResults(self):
    """ Report results as fomatted string of key and value pairs.
    """
    kv = self.results.items()
    return formatkv(kv)

def ReporterInspect(name):
    """ This decorator for a function will store a specified 
        argument value for the given argument name.
    """
    def wrap(function):
        @wraps(function)
        def checkedFunction(self, *args, **kwargs):
            if name in kwargs:
                self.storeParameter(function.__name__, name, kwargs[name])
            function(self, *args, **kwargs)
        return checkedFunction
    return wrap

def ReporterCheck(function):
  """ This decorator for a function will store a success result
      if no exception is thrown while executing the function.
  """
  @wraps(function)
  def checkedFunction(self, *args, **kwargs):
    try:
      function(self, *args, **kwargs)
      self.storeResult(function.__name__, True)
    except:
      self.storeResult(function.__name__, False)
      raise
  return checkedFunction

def ReporterCheckResult(function):
  """ This decorator will store the result of the function call
      if no exception is thrown while executing the function.
  """
  @wraps(function)
  def checkedFunction(self, *args, **kwargs):
    try:
      result = function(self, *args, **kwargs)
      self.storeResult(function.__name__, result)
    except:
      self.storeResult(function.__name__, False)
      raise
  return checkedFunction
