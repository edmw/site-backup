# coding: utf-8

from backup.source.humhub import HH, HHError
from backup.source.wordpress import WP, WPError

from .error import SourceErrors

class SourceFactory(object):
    def __init__(self, path):
        super(SourceFactory, self).__init__()
        self.path = path

    def create(self, **kwargs):
        errors = []

        try:
            source = WP(self.path, **kwargs)
        except WPError as exception:
            errors.append(exception)
        else:
            return source

        try:
            source = HH(self.path, **kwargs)
        except HHError as exception:
            errors.append(exception)
        else:
            return source

        raise SourceErrors("Can't create source", errors)
            
