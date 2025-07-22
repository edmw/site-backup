"""
##     ##    ###    ##     ## ##       ######## ##      ##    ###    ########  ########  ######## ##    ##
##     ##   ## ##   ##     ## ##          ##    ##  ##  ##   ## ##   ##     ## ##     ## ##       ###   ##
##     ##  ##   ##  ##     ## ##          ##    ##  ##  ##  ##   ##  ##     ## ##     ## ##       ####  ##
##     ## ##     ## ##     ## ##          ##    ##  ##  ## ##     ## ########  ##     ## ######   ## ## ##
 ##   ##  ######### ##     ## ##          ##    ##  ##  ## ######### ##   ##   ##     ## ##       ##  ####
  ## ##   ##     ## ##     ## ##          ##    ##  ##  ## ##     ## ##    ##  ##     ## ##       ##   ###
   ###    ##     ##  #######  ########    ##     ###  ###  ##     ## ##     ## ########  ######## ##    ##
"""

import json
from pathlib import Path

from backup.reporter import reporter_check
from backup.utils import slugify

from ._base import Source, SourceConfig
from .errors import SourceError


class VWError(SourceError):
    def __init__(self, vw, message):
        super().__init__()
        self.vw = vw
        self.message = message

    def __str__(self):
        return f"VWError({self.message!r})"


class VWNotFoundError(VWError):
    pass


class VW(Source):
    def __init__(self, path: Path, config: SourceConfig | None = None):
        super().__init__(path, path / "config.json")

        if not self._check_configuration():
            raise VWNotFoundError(
                self, f"no vaultwarden instance found at '{self.fspath}'"
            )

        self._parse_configuration()

        self.dbname = None
        self.dbhost = None

        self.slug = slugify(self.title)

    def _check_configuration(self) -> bool:
        return self.fspath.exists() and self.fsconfig.is_file()

    @reporter_check
    def _parse_configuration(self) -> None:
        try:
            with self.fsconfig.open("r", encoding="utf-8") as f:
                config_data = json.load(f)
            self.title = config_data["domain"]
            self.description = f"Vaultwarden '{self.title}'"
            self.email = config_data["smtp_from"]
        except json.JSONDecodeError as e:
            raise VWError(self, f"Invalid JSON in config file: {e}") from e
        except KeyError as e:
            raise VWError(self, f"Missing key in config file: {e}") from e
