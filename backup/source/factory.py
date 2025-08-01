from pathlib import Path

from backup.source.humhub import HH, HHError
from backup.source.vaultwarden import VW, VWError
from backup.source.wordpress import WP, WPError

from ._base import Source, SourceConfig
from .errors import SourceMultipleError


class SourceFactory:
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def create(self, config: SourceConfig) -> Source:
        errors: list[Exception] = []

        try:
            source = WP(self.path, config)
        except WPError as exception:
            errors.append(exception)
        else:
            return source

        try:
            source = HH(self.path, config)
        except HHError as exception:
            errors.append(exception)
        else:
            return source

        try:
            source = VW(self.path, config)
        except VWError as exception:
            errors.append(exception)
        else:
            return source

        raise SourceMultipleError("Can't create source", errors)
