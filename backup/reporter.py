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
    self.results = dict()

  def storeResult(self, name, result):
    """ Store result for the given name.

        For consecutive calls with the same name results
        will be stored in a list.
    """
    name = re_camel.sub(r" \1", name.strip('_')).upper()
    if name in self.results:
      if type(self.results[name]) == type(list()):
        self.results[name].append(result)
      else:
        self.results[name] = [self.results[name], result]        
    else:
      self.results[name] = result

  def reportResults(self):
    """ Report results as fomatted string of key and value pairs.
    """
    return formatkv(self.results.iteritems())

def ReporterCheck(function):
  """ This decorator for a function will store a success result
      if no exception is thrown while executing the function.
  """
  @wraps(function)
  def checkedFunction(self, *args, **kwargs):
    try:
      function(self, *args, **kwargs)
      self.storeResult(function.func_name, True)
    except:
      self.storeResult(function.func_name, False)
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
      self.storeResult(function.func_name, result)
    except:
      self.storeResult(function.func_name, False)
      raise
  return checkedFunction
