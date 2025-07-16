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

import os
import logging

from backup.utils import formatkv
from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult


class FSError(Exception):
    def __init__(self, fs, message):
        self.fs = fs
        self.message = message

    def __str__(self):
        return "FSError({!r})".format(self.message)


class FSNotFoundError(FSError):
    pass


class FS(Reporter, object):
    def __init__(self, path):
        super(FS, self).__init__()

        self.path = path

        if not os.path.exists(self.path):
            raise FSNotFoundError(self, "path '{}' not found".format(self.path))

    def __str__(self):
        return formatkv(
            [
                ("FS", self.path),
            ],
            title="FILESYSTEM",
        )

    @ReporterCheck
    def addToArchive(self, archive):
        logging.debug("add path '{}' to archive '{}'".format(self.path, archive.name))
        archive.addPath(self.path, name=archive.name)
