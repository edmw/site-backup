__version__ = "1.0.0"

import re

from backup.utils import formatkv

re_camel = re.compile(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))")

class ReporterMixin(object):
  def __init__(self):
    self.results = dict()

  def setResult(self, name, result):
    name = re_camel.sub(r" \1", name.strip('_')).upper()
    self.results[name] = result

  def checkException(self, function, *arguments):
    try:
      function(*arguments)
      self.setResult(function.func_name, True)
    except:
      self.setResult(function.func_name, False)
      raise

  def checkResultAndException(self, function, *arguments):
    try:
      self.setResult(function.func_name, function(*arguments))
    except:
      self.setResult(function.func_name, False)
      raise

  def report(self):
  	return str(self) + '\n' + formatkv(self.results.iteritems())
