# coding: utf-8

from typing import TypedDict

from backup.source.humhub import HH, HHError
from backup.source.wordpress import WP, WPError

from .error import SourceErrors


class SourceConfig(TypedDict, total=False):
    """Configuration parameters for source instances."""

    dbname: str
    dbhost: str
    dbport: int
    dbuser: str
    dbpass: str
    dbprefix: str


class SourceFactory(object):
    def __init__(self, path: str) -> None:
        super(SourceFactory, self).__init__()
        self.path = path

    def create(
        self, **kwargs: SourceConfig
    ) -> WP | HH:  # TODO: Consider creating a common base interface for WP and HH
        errors: list[Exception] = []

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
