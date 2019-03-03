# coding: utf-8

class SourceError(Exception):
    pass

class SourceErrors(Exception):
    def __init__(self, message, errors):
        super(SourceErrors, self).__init__(message + (": {}".format([str(e) for e in errors])))
        self.errors = errors

