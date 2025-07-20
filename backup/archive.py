"""
   ###    ########   ######  ##     ## #### ##     ## ########
  ## ##   ##     ## ##    ## ##     ##  ##  ##     ## ##
 ##   ##  ##     ## ##       ##     ##  ##  ##     ## ##
##     ## ########  ##       #########  ##  ##     ## ######
######### ##   ##   ##       ##     ##  ##   ##   ##  ##
##     ## ##    ##  ##    ## ##     ##  ##    ## ##   ##
##     ## ##     ##  ######  ##     ## ####    ###    ########
"""

from __future__ import annotations

import collections
import io
import logging
import os
import tarfile
import time
from pathlib import Path

import humanfriendly

from backup.reporter import Reporter, reporter_check, reporter_check_result
from backup.utils import formatkv, timestamp2date, timestamp4now


class ArchiveResult(collections.namedtuple("Result", ["size"])):
    """Class for results of archive operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        size = humanfriendly.format_size(self.size)
        return f"Result(size={size})"


class ArchiveFile:
    def __init__(self, name: str, binmode: bool = False) -> None:
        super().__init__()

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

    def fileobject(self) -> io.BytesIO:
        self.handle.seek(0)
        return self.handle


class Archive(Reporter):
    def __init__(self, label: str, timestamp: str | None = None) -> None:
        super().__init__()

        self.timestamp = timestamp or timestamp4now()

        self.name = f"{label}-{self.timestamp}"
        self.path = "."

        self.ctime = timestamp2date(self.timestamp)

        self.filename = f"{self.name}.tgz"

        self.tar = None

    @classmethod
    def fromfilename(cls, filename: str, check_label: str | None = None) -> Archive:
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

    def __repr__(self) -> str:
        return f"Archive[name={self.name}, timestamp={self.timestamp}]"

    def __str__(self) -> str:
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

        self.store_result(
            "createArchive", ArchiveResult(os.path.getsize(self.tarname()))
        )

    def create_archive_file(self, name: str, binmode: bool = False) -> ArchiveFile:
        return ArchiveFile(name, binmode=binmode)

    @reporter_check_result
    def add_archive_file(self, archivefile: ArchiveFile) -> str:
        if self.tar:
            tarinfo = tarfile.TarInfo(archivefile.name)
            tarinfo.mtime = archivefile.mtime
            tarinfo.size = archivefile.size()
            self.tar.addfile(tarinfo, archivefile.fileobject())
            return archivefile.name
        else:
            raise RuntimeError("archive not opened")

    @reporter_check_result
    def add_path(self, path: Path, name: str | None = None) -> Path:
        if self.tar:
            self.tar.add(str(path), arcname=name)
            return path
        else:
            raise RuntimeError("archive not opened")

    @reporter_check
    def add_manifest(self, timestamp: str) -> None:
        f = self.create_archive_file("MANIFEST")
        f.writeline(f"Timestamp: {timestamp}")
        self.add_archive_file(f)

    @reporter_check_result
    def rename(self, path):
        tarname = self.tarname()
        if not path == self.path:
            self.path = path
            destination_tarname = self.tarname()
            os.rename(tarname, destination_tarname)
            tarname = destination_tarname
        return tarname

    @reporter_check_result
    def remove(self) -> str:
        tarname = self.tarname()
        if os.path.isfile(tarname):
            os.remove(tarname)
        return tarname
