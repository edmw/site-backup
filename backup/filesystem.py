# coding: utf-8

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

from backup.reporter import Reporter, ReporterCheck
from backup.utils import formatkv


class FSError(Exception):
    def __init__(self, fs: "FS", message: str) -> None:
        self.fs = fs
        self.message = message

    def __str__(self) -> str:
        return f"FSError({self.message!r})"


class FSNotFoundError(FSError):
    pass


class FS(Reporter, object):
    def __init__(self, path: str) -> None:
        super(FS, self).__init__()

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

    @ReporterCheck
    def addToArchive(self, archive):
        logging.debug("add path '%s' to archive '%s'", self.path, archive.name)
        archive.addPath(self.path, name=archive.name)
