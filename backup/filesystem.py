"""
######## #### ##       ########  ######  ##    ##  ######  ######## ######## ##     ##
##        ##  ##       ##       ##    ##  ##  ##  ##    ##    ##    ##       ###   ###
##        ##  ##       ##       ##         ####   ##          ##    ##       #### ####
######    ##  ##       ######    ######     ##     ######     ##    ######   ## ### ##
##        ##  ##       ##             ##    ##          ##    ##    ##       ##     ##
##        ##  ##       ##       ##    ##    ##    ##    ##    ##    ##       ##     ##
##       #### ######## ########  ######     ##     ######     ##    ######## ##     ##
"""

import logging
import os

from backup.reporter import Reporter, reporter_check
from backup.utils import formatkv


class FSError(Exception):
    def __init__(self, fs: "FS", message: str) -> None:
        self.fs = fs
        self.message = message

    def __str__(self) -> str:
        return f"FSError({self.message!r})"


class FSNotFoundError(FSError):
    pass


class FS(Reporter):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.path = path

        if not os.path.exists(self.path):
            raise FSNotFoundError(self, f"path '{self.path}' not found")

    def __str__(self) -> str:
        return formatkv(
            [
                ("FS", self.path),
            ],
            title="FILESYSTEM",
        )

    @reporter_check
    def add_to_archive(self, archive):
        logging.debug("add path '%s' to archive '%s'", self.path, archive.name)
        archive.add_path(self.path, name=archive.name)
