"""
Mixin and Decorators to collect and report
success and failure of function calls.

To use add the mixin to a class
and decorate the functions to be observed:

class IDoSomething(Reporter):

    @reporter_check
    def doSomething(self):
        ...

    @reporter_check_result
    def iWillReturnAResult(self):
        ...

Then call object.reportResults() any time to generate a report.
"""

import re
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any

from backup.utils import formatkv

# regular expression to convert camel case to space separated words
re_camel = re.compile(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))")


class Reporter:
    """Mixin to store and report success and failure of function calls."""

    def __init__(self) -> None:
        self.parameters: OrderedDict[str, Any] = OrderedDict()
        self.results: OrderedDict[str, Any] = OrderedDict()

    def store_parameter(self, fname: str, name: str, value: Any) -> None:
        """Store parameter and value for the given function.

        For consecutive calls with the same function name
        parameters will be stored in a list.
        """
        fname = re_camel.sub(r" \1", fname.strip("_")).upper()
        if fname in self.parameters:
            if type(self.parameters[fname]) is list:
                self.parameters[fname].append((name, value))
            else:
                self.parameters[fname] = [self.parameters[fname], (name, value)]
        else:
            self.parameters[fname] = (name, value)

    def store_result(self, fname: str, result: Any) -> None:
        """Store result for the given function.

        For consecutive calls with the same function name
        results will be stored in a list.
        """
        fname = re_camel.sub(r" \1", fname.strip("_")).upper()
        if fname in self.results:
            if type(self.results[fname]) is list:
                self.results[fname].append(result)
            else:
                self.results[fname] = [self.results[fname], result]
        else:
            self.results[fname] = result

    def report_parameters(self) -> str:
        """Report parameters as formatted string of key and value pairs."""
        kv = []
        for fname, parameters in self.parameters.items():
            if type(parameters) is list:
                for name, value in parameters:
                    kv.append((f"{fname}({name})", value))
            elif type(parameters) is tuple:
                name, value = parameters
                kv.append((f"{fname}({name})", value))
            else:
                kv.append((fname, parameters))
        return formatkv(kv)

    def report_results(self) -> str:
        """Report results as fomatted string of key and value pairs."""
        kv = self.results.items()
        return formatkv(kv)


def reporter_inspect(name: str) -> Callable[[Callable], Callable]:
    """This decorator for a function will store a specified
    argument value for the given argument name.
    """

    def wrap(function: Callable) -> Callable:
        @wraps(function)
        def checked_function(self, *args, **kwargs):
            if name in kwargs:
                self.store_parameter(function.__name__, name, kwargs[name])
            return function(self, *args, **kwargs)

        return checked_function

    return wrap


def reporter_check(function: Callable) -> Callable:
    """This decorator for a function will store a success result
    if no exception is thrown while executing the function.
    """

    @wraps(function)
    def checked_function(self, *args, **kwargs):
        try:
            function(self, *args, **kwargs)
            self.store_result(function.__name__, True)
        except BaseException:
            self.store_result(function.__name__, False)
            raise

    return checked_function


def reporter_check_result(function: Callable) -> Callable:
    """This decorator will store the result of the function call
    if no exception is thrown while executing the function.
    """

    @wraps(function)
    def checked_function(self, *args, **kwargs):
        try:
            result = function(self, *args, **kwargs)
            self.store_result(function.__name__, result)
            return result
        except BaseException:
            self.store_result(function.__name__, False)
            raise

    return checked_function
