# coding: utf-8

"""
   ###    ########   ######  ##     ## #### ##     ## ########
  ## ##   ##     ## ##    ## ##     ##  ##  ##     ## ##
 ##   ##  ##     ## ##       ##     ##  ##  ##     ## ##
##     ## ########  ##       #########  ##  ##     ## ######
######### ##   ##   ##       ##     ##  ##   ##   ##  ##
##     ## ##    ##  ##    ## ##     ##  ##    ## ##   ##
##     ## ##     ##  ######  ##     ## ####    ###    ########
"""

import collections
import io
import logging
import os
import tarfile
import time

import humanfriendly

from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult
from backup.utils import formatkv, timestamp2date, timestamp4now


class ArchiveResult(collections.namedtuple("Result", ["size"])):
    """Class for results of archive operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        size = humanfriendly.format_size(self.size)
        return f"Result(size={size})"


class ArchiveFile(object):
    def __init__(self, name: str, binmode: bool = False) -> None:
        super(ArchiveFile, self).__init__()

        self.name = name

        self.binmode = binmode

        self.ctime = time.time()
        self.mtime = self.ctime

        self.handle = io.BytesIO()

    def write(self, data: str | bytes) -> None:
        if isinstance(data, str):
            self.handle.write(data.encode() if not self.binmode else data.encode())
        else:
            self.handle.write(data)

    def writeline(self, data: str | bytes) -> None:
        if isinstance(data, str):
            self.handle.write(data.encode() if not self.binmode else data.encode())
        else:
            self.handle.write(data)
        self.handle.write(b"\n")

    def size(self) -> int:
        self.handle.seek(0, os.SEEK_END)
        return self.handle.tell()

    def fileobject(self):
        self.handle.seek(0)
        return self.handle


class Archive(Reporter, object):
    def __init__(self, label, timestamp=None):
        super(Archive, self).__init__()

        self.timestamp = timestamp or timestamp4now()

        self.name = f"{label}-{self.timestamp}"
        self.path = "."

        self.ctime = timestamp2date(self.timestamp)

        self.filename = f"{self.name}.tgz"

        self.tar = None

    @classmethod
    def fromfilename(cls, filename, check_label=None):
        import re

        m = re.match(r"^(.*)-([^-]+)\.tgz$", filename)
        if not m:
            raise ValueError(f"filename '{filename}' invalid format")

        label, timestamp = m.groups()

        if check_label and label != check_label:
            raise ValueError(
                f"filename '{filename}' not matching label '{check_label}'"
            )

        return cls(label, timestamp)

    def __repr__(self):
        return f"Archive[name={self.name}, timestamp={self.timestamp}]"

    def __str__(self):
        return formatkv([("Name", self.name)], title="ARCHIVE")

    def tarname(self, path=None):
        if not path:
            path = self.path
        return os.path.join(path, self.filename)

    def __enter__(self):
        self.tar = tarfile.open(
            self.tarname(),
            "w:gz",
            debug=1 if logging.getLogger().getEffectiveLevel() == logging.DEBUG else 0,
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.tar:
            self.tar.close()
        else:
            raise RuntimeError("archive not opened")

        self.storeResult(
            "createArchive", ArchiveResult(os.path.getsize(self.tarname()))
        )

    def createArchiveFile(self, name, binmode=False):
        return ArchiveFile(name, binmode=binmode)

    @ReporterCheckResult
    def addArchiveFile(self, archivefile):
        if self.tar:
            tarinfo = tarfile.TarInfo(archivefile.name)
            tarinfo.mtime = archivefile.mtime
            tarinfo.size = archivefile.size()
            self.tar.addfile(tarinfo, archivefile.fileobject())
            return archivefile.name
        else:
            raise RuntimeError("archive not opened")

    @ReporterCheckResult
    def addPath(self, path, name=None):
        if self.tar:
            self.tar.add(path, arcname=name)
            return path
        else:
            raise RuntimeError("archive not opened")

    @ReporterCheck
    def addManifest(self, timestamp):
        f = self.createArchiveFile("MANIFEST")
        f.writeline(f"Timestamp: {timestamp}")
        self.addArchiveFile(f)

    @ReporterCheckResult
    def rename(self, path):
        tarname = self.tarname()
        if not path == self.path:
            self.path = path
            destination_tarname = self.tarname()
            os.rename(tarname, destination_tarname)
            tarname = destination_tarname
        return tarname

    @ReporterCheckResult
    def remove(self):
        tarname = self.tarname()
        if os.path.isfile(tarname):
            os.remove(tarname)
        return tarname
